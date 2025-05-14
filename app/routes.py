import os
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app, abort
from app import db
from app.models import Phrase, Conversation, ConversationLine
from app.services.translation import translate_to_korean, generate_conversation_scenario
from app.services.audio import generate_audio
from app.utils.validators import validate_phrase
from functools import wraps
import time
from app.utils.audio_merge import merge_audio_files
import traceback

main = Blueprint("main", __name__)

# Simple rate limiter
request_history = {}


def rate_limit(limit_per_minute=10):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            ip = request.remote_addr
            current_time = time.time()

            # Initialize or clean up old requests
            if ip not in request_history:
                request_history[ip] = []
            request_history[ip] = [
                t for t in request_history[ip] if current_time - t < 60
            ]

            # Check if rate limit exceeded
            if len(request_history[ip]) >= limit_per_minute:
                current_app.logger.warning(f"Rate limit exceeded for IP: {ip}")
                abort(429)

            # Add current request
            request_history[ip].append(current_time)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/library")
def library():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    phrases = Phrase.query.order_by(Phrase.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template("library.html", phrases=phrases)


@main.route("/api/translate", methods=["POST"])
@rate_limit(limit_per_minute=10)
def api_translate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        english_text = data.get("text", "").strip()

        # Validate input
        is_valid, error_msg = validate_phrase(english_text)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Translate to Korean
        current_app.logger.info(f"Translating: {english_text}")
        korean_text = translate_to_korean(english_text)

        # Create unique filename with UUID to avoid collisions
        unique_id = str(uuid.uuid4())[:8]
        safe_text = "".join(
            c for c in english_text.lower().replace(" ", "_") if c.isalnum() or c == "_"
        )
        filename = f"{safe_text[:30]}_{unique_id}.mp3"
        filepath = os.path.join(current_app.config["AUDIO_DIR"], filename)

        # Generate audio
        current_app.logger.info(f"Generating audio for: {korean_text}")
        generate_audio(korean_text, filepath)
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            current_app.logger.error(f"Audio file not created or empty: {filepath}")
            raise RuntimeError(f"Audio file not created or empty: {filepath}")

        # Save to database
        phrase = Phrase(
            english_text=english_text,
            korean_text=korean_text,
            audio_path=f"/static/audio/{filename}",
        )
        db.session.add(phrase)
        db.session.commit()

        return jsonify(phrase.to_dict())

    except ValueError as e:
        current_app.logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Translation API error: {str(e)}")
        return jsonify(
            {"error": "An error occurred during translation or audio generation"}
        ), 500


@main.route("/api/phrases", methods=["GET"])
def api_phrases():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 20

        phrases = Phrase.query.order_by(Phrase.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify(
            {
                "phrases": [p.to_dict() for p in phrases.items],
                "total": phrases.total,
                "pages": phrases.pages,
                "current_page": page,
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error fetching phrases: {str(e)}")
        return jsonify({"error": "Failed to retrieve phrases"}), 500


@main.route("/api/conversation", methods=["POST"])
@rate_limit(limit_per_minute=5)
def api_conversation():
    try:
        data = request.get_json()
        if not data or not data.get("prompt"):
            return jsonify({"error": "No scenario prompt provided"}), 400
        prompt = data["prompt"].strip()
        if not prompt:
            return jsonify({"error": "Prompt cannot be empty"}), 400

        # Generate conversation scenario
        scenario = generate_conversation_scenario(prompt)
        title = scenario.get("title", "Conversation")
        description = scenario.get("description", "")
        lines = scenario["lines"]

        # Speaker to OpenAI voice mapping
        speaker_voices = {1: "onyx", 2: "nova"}
        audio_dir = current_app.config["AUDIO_DIR"]
        audio_paths = []
        phrase_objs = []
        conversation_lines = []

        for idx, line in enumerate(lines):
            speaker = line.get("speaker", 1)
            english_text = line.get("english_text", "").strip()
            korean_text = line.get("korean_text", "").strip()
            if not english_text or not korean_text:
                continue
            # Generate unique filename
            unique_id = str(uuid.uuid4())[:8]
            safe_text = "".join(
                c
                for c in english_text.lower().replace(" ", "_")
                if c.isalnum() or c == "_"
            )
            filename = f"conv_{safe_text[:20]}_{unique_id}.mp3"
            filepath = os.path.join(audio_dir, filename)
            # Generate audio for this line
            generate_audio(
                korean_text, filepath, voice=speaker_voices.get(speaker, "onyx")
            )
            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                current_app.logger.error(f"Audio file not created or empty: {filepath}")
                raise RuntimeError(f"Audio file not created or empty: {filepath}")
            audio_rel_path = f"/static/audio/{filename}"
            audio_paths.append(filepath)
            # Save phrase
            phrase = Phrase(
                english_text=english_text,
                korean_text=korean_text,
                audio_path=audio_rel_path,
            )
            db.session.add(phrase)
            db.session.flush()  # Get phrase.id
            phrase_objs.append(phrase)
            # Save conversation line
            conv_line = ConversationLine(
                speaker=f"Speaker {speaker}",
                order=idx,
                phrase_id=phrase.id,
            )
            conversation_lines.append(conv_line)

        # Merge audio files
        merged_filename = f"conversation_{str(uuid.uuid4())[:8]}.mp3"
        merged_filepath = os.path.join(audio_dir, merged_filename)
        merge_audio_files(audio_paths, merged_filepath, pause_seconds=1.5)
        merged_audio_rel_path = f"/static/audio/{merged_filename}"

        # Save conversation
        conversation = Conversation(
            title=title,
            description=description,
            audio_path=merged_audio_rel_path,
        )
        db.session.add(conversation)
        db.session.flush()  # Get conversation.id
        # Link lines to conversation
        for conv_line in conversation_lines:
            conv_line.conversation_id = conversation.id
            db.session.add(conv_line)
        db.session.commit()

        return jsonify(conversation.to_dict())
    except Exception as e:
        current_app.logger.error(
            f"Conversation API error: {str(e)}\n{traceback.format_exc()}"
        )
        return jsonify(
            {"error": f"An error occurred during conversation generation: {str(e)}"}
        ), 500


@main.route("/api/conversations", methods=["GET"])
def api_conversations():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 10
        conversations = Conversation.query.order_by(
            Conversation.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify(
            {
                "conversations": [c.to_dict() for c in conversations.items],
                "total": conversations.total,
                "pages": conversations.pages,
                "current_page": page,
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error fetching conversations: {str(e)}")
        return jsonify({"error": "Failed to retrieve conversations"}), 500


@main.route("/api/conversations/<int:conversation_id>", methods=["GET"])
def api_conversation_detail(conversation_id):
    try:
        conversation = Conversation.query.get_or_404(conversation_id)
        return jsonify(conversation.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error fetching conversation detail: {str(e)}")
        return jsonify({"error": "Failed to retrieve conversation"}), 500


@main.route("/conversations")
def conversations():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    conversations = Conversation.query.order_by(
        Conversation.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("conversations.html", conversations=conversations)


@main.route("/conversations/<int:conversation_id>")
def conversation_detail(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    return render_template("conversation_detail.html", conversation=conversation)


@main.route("/conversations/new")
def new_conversation():
    return render_template("new_conversation.html")
