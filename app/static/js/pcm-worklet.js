// Microphone tap for the Gemini Live transport. Runs off the main thread,
// batches input into ~2048-frame blocks (about 40 ms at 48 kHz) and posts them;
// the page converts each block to 16 kHz PCM16 and sends it over the socket.
// Posting every 128-frame render quantum would be ~375 messages a second.
const CHUNK_FRAMES = 2048;

class PcmTap extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(CHUNK_FRAMES);
    this.offset = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0] || !input[0].length) {
      return true;
    }
    const data = input[0];
    let index = 0;
    while (index < data.length) {
      const take = Math.min(CHUNK_FRAMES - this.offset, data.length - index);
      this.buffer.set(data.subarray(index, index + take), this.offset);
      this.offset += take;
      index += take;
      if (this.offset === CHUNK_FRAMES) {
        this.port.postMessage(this.buffer.slice(0));
        this.offset = 0;
      }
    }
    return true;
  }
}

registerProcessor("pcm-tap", PcmTap);
