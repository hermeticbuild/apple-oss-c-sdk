# IOKit audio types

Copy `IOAudioTypes.h` verbatim from Apple OSS IOAudioFamily-740.1 to
`Headers/audio/IOAudioTypes.h`. The pinned source file carries an Apple
Public Source License notice. Preserve it and use the pinned project's
license for the distribution inventory.
[Source header](https://github.com/apple-oss-distributions/IOAudioFamily/blob/6fdf514055a9868fe20e4dc3845b78dfa5e27110/IOAudioTypes.h)
· [Project license](https://github.com/apple-oss-distributions/IOAudioFamily/blob/6fdf514055a9868fe20e4dc3845b78dfa5e27110/APPLE_LICENSE)

The recipe preserves the audio profile's empty IOKit stub. Its scope is
the userspace audio types header. The [ABI probe](test.c) checks record sizes
and field offsets against the macOS 26.5 ABI for arm64 and x86_64.
