# The Signature Voice

The controlled comparison uses the original Mission 004.2 storyboard, script, voice-rate audit and claim ledger. The original MP4 remains the editorial benchmark. For Pocket TTS, each move preserves its position relative to the spoken thought where possible. Intentional lead and tail holds, camera directions, editorial cuts, captions, legal PGN replay and board positions come from the frozen edit.

[Original review film](https://chatgpt.com/library?file_id=libfile_ce9d9f2e151c8191bfe9a5b4aa1eee21&account_id=personal) · [Original production artifact](https://github.com/ReidMaxim/CHECKMATE-STUDIO/actions/runs/44985067227/artifacts/14739048994)

## Model and voice rights

- Pocket TTS 3.1.0 runs with CPU PyTorch 2.8.0 in a dedicated environment. The adapter uses the documented model and voice-state APIs with pinned, SHA-256-verified English weights and upstream voice states from the public checkpoint. The model card declares CC BY 4.0. [Pocket TTS API](https://kyutai-labs.github.io/pocket-tts/) · [Pinned public checkpoint](https://huggingface.co/kyutai/pocket-tts-without-voice-cloning/tree/d29db7978e464fb90cb3359ee0c69a273b9142cc)
- Alba is Kyutai’s published Casual voice-acted profile by Alba MacKenna. Anna is Kyutai’s published VCTK p228 profile. Both reference sources permit commercial reuse under CC BY 4.0 with attribution. The pipeline uses the upstream precomputed profiles and presents them as synthetic voices. Preserve the credits in the profile file and keep personal likeness and endorsement separate from the asset license. [Kyutai voice source and licenses](https://huggingface.co/kyutai/tts-voices) · [VCTK corpus](https://datashare.ed.ac.uk/handle/10283/3443) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Vosk small US English 0.15 is the pinned Apache-2.0 review recognizer. Its transcript differences are leads for a listener. Accent, timing, repeated words and named squares require listening review. [Vosk models](https://alphacephei.com/vosk/models)
- Chatterbox Nano is a CPU-capable MIT alternative. Its upstream is archived, and an independently verified female reference would add a separate validation path. The comparison focuses on Pocket TTS and Kokoro. [Chatterbox repository](https://github.com/resemble-ai/chatterbox) · [Nano weights](https://huggingface.co/ResembleAI/chatterbox-nano)

## Production

The Signature Voice workflow installs pinned dependencies separately and caches checksum-verified model downloads. It synthesizes all three full scripts and all three terminology reads with the same loudness target. Each full read exports a dry audition. The selected Pocket profile also gets a full vertical render with the original effects. The workflow records generation time per thought, signal statistics, effective timing, transcripts and disputed terms. Use the workflow input to render the other Pocket profile once manual dispatch is available from the default branch.

The channel profile stays provisional until human review. The Kokoro adapter wraps the existing voice studio and uses its established bounded retries. Pocket uses native tempo, two seeded attempts, and the same signal gate and timeline renderer.
