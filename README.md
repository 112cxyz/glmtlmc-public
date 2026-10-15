# glmtlmc

Minecraft on Apple Silicon with a real OpenGL 4.6 stack:
Minecraft 26.2 -> Zink -> KosmicKrisp (Vulkan) -> Metal 4.

Fully self-contained. Nothing is installed on your machine — the game is
launched using the files inside this folder, and deleting this folder
removes every trace (run Unpatch first).

## Requirements
- Apple Silicon Mac, macOS 27.0+ (Metal 4)
- Prism Launcher
- Minecraft 26.2 instance (Iris/Sodium for shaders)

## Use
1. Quit Prism Launcher completely
2. Run `./glmtlmc` (double-click works too)
3. Paste the path of your instance when asked, then choose `1 : Patch`
4. Open Prism Launcher and launch the instance

To undo: `./glmtlmc` -> `2 : Unpatch`
After moving this folder: `./glmtlmc` -> `3 : Update glmtlmc`

You can move, rename or copy this folder anywhere. Every shipped library finds
its siblings through `@loader_path`, and nothing is installed outside this
folder. Install names were relocated when this package was assembled; Mesa's
own compile-time drirc search paths still name the prefix it was built in,
but they are harmless fallbacks — on any other machine those paths do not
exist, and Mesa simply uses its built-in defaults.

## VR
`4 : Patch + VR (MoltenVR)` works out of the box; two things in here make it:

- `stack/vr-lib/` — the search path DYLD_LIBRARY_PATH points at in VR mode. It
  mirrors `stack/lib/` without `libGL.dylib` and the `libglfw*` pair, so Apple's
  own libGL survives alongside Mesa's instead of being shadowed by it.
- `stack/vr-lib/libvr_glfix.dylib` — an interposer that keeps MoltenVR's shim
  off a null-CGL segfault. It is built from `scripts/vr-glfix/vr_glfix.c`, which
  ships beside it so you can read the 300 lines or rebuild it yourself:

      xcrun clang -arch arm64 -O2 -Wall -Wextra -dynamiclib \
          -install_name @rpath/libvr_glfix.dylib -framework OpenGL \
          scripts/vr-glfix/vr_glfix.c -o stack/vr-lib/libvr_glfix.dylib
      codesign --force --sign - stack/vr-lib/libvr_glfix.dylib

  `glmtlmc` measures the shipped copy before it will use it (25 redirects, a
  400-byte interpose table, no bound CGL symbols, a valid signature) and
  rebuilds it from that source if it ever disagrees.

Shaderpacks work with Iris. Third-party shaderpacks are not included in this
package. To create a local Complementary Reimagined copy later, see
`shaders/ComplementaryPatch/README.md`.

The optional tools download upstream content only when run explicitly; nothing
patched is included in this package.

The shader tool requires its shipped patch file at
`shaders/ComplementaryPatch/patches/001-remove-apple-device-gating.patch`.

The Voxy tool at `mods/VoxyMacPatch/README.md` downloads Voxy from Modrinth and
builds a macOS-patched jar in its own `dist/` folder. It exists because Voxy
ships no Apple Silicon native libraries, so it cannot open a world on macOS
without them. The patched jar stays on your machine: Voxy is all rights
reserved and forbids redistributing unofficial versions.

Licenses: `licenses/`
