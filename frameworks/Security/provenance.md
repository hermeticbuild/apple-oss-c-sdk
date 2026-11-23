# Security authorization headers

Stage the public `Authorization.h` from the Security gitlink in Apple's
macOS 26.5 OSS distribution. It supplies `AuthorizationRef` for
SystemConfiguration. This header layer covers authorization declarations.
The test checks the public handle type on both architectures.

- [Security source and notices](https://github.com/apple-oss-distributions/Security/blob/97c3a4296c1ea06b0fe1877a7e616aa84450b5b2/OSX/libsecurity_authorization/lib/Authorization.h)
- [macOS 26.5 OSS distribution](https://github.com/apple-oss-distributions/distribution-macOS/tree/83390100289cedfe669c31a96c94326d31afa1ed)
