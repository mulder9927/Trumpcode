# Installing TrumpLang

> *"The installation is very simple. Incredibly simple. We made it simple on purpose because, frankly, it should be simple. That's what smart people do — they make things simple."*

---

## Requirements

You need a few things before you can install TrumpLang. These are standard tools. The best tools. Every serious computer has them.

- **Linux or macOS** — Windows support is coming. We're working on it. Tremendous work being done.
- **GCC** (version 8 or later) or **Clang**
- **GNU Make**
- **zlib** development headers
- About **1.5 GB of disk space** — we don't do things small

### Installing Requirements on Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y build-essential zlib1g-dev libffi-dev
```

### Installing Requirements on macOS

```bash
xcode-select --install
brew install zlib
```

---

## Build and Install

### Step 1 — Clone the Repository

```bash
git clone https://github.com/[your-org]/TrumpCode.git
cd TrumpCode
```

### Step 2 — Configure

```bash
./configure --prefix=/usr/local
```

If you want it installed somewhere else — maybe you don't have root access, which is fine, we understand, not everyone is a winner — do this instead:

```bash
./configure --prefix=$HOME/.local
```

### Step 3 — Build

```bash
make -j$(nproc) trump
```

This builds the `trump` binary. The `-j$(nproc)` flag uses all your cores. All of them. **Maximum power.** It will take a few minutes. Tremendous things take time.

### Step 4 — Install

```bash
sudo make install
```

Or without root:

```bash
make install
```

### Step 5 — Verify

```bash
trump --version
```

You should see something like:

```
TrumpLang 1.0 (The Best Version)
```

If you see that, **you're done.** You now have TrumpLang installed on your machine. Congratulations. You made a good decision today.

---

## Running Your First Program

Create a file called `hello.trump`:

```trump
LOOK, FOLKS("Hello, America!")
LOOK, FOLKS("TrumpLang is installed and running. Perfectly.")
```

Run it:

```bash
trump hello.trump
```

Output:

```
Hello, America!
TrumpLang is installed and running. Perfectly.
```

**That's it.** You're writing TrumpLang. You're a TrumpLang developer now.

---

## Adding `trump` to Your PATH

If the `trump` command isn't found after installation, you need to add it to your PATH. This is very standard. Very easy. I'm surprised you don't already know this, but that's okay — not everyone knows everything. I do, but that's different.

### For bash

```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### For zsh

```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## AI-Assisted Development

TrumpLang was **designed** to be written with AI assistance. The language has multiple valid phrases for every keyword — six ways to say `if`, five ways to say `return`, seven ways to say `def`. Nobody memorizes all of that.

The recommended workflow:

1. Describe what you want your program to do in plain English
2. Ask your AI assistant (Claude works great — very smart, very fast) to write it in TrumpLang
3. Save the output as a `.trump` file
4. Run it with `trump myfile.trump`

This is the future of programming. AI writes the code. You own it. Beautiful.

---

## Troubleshooting

### "trump: command not found"

Your PATH doesn't include the install directory. See the PATH section above.

### Build fails with missing header errors

You're missing development libraries. On Ubuntu: `sudo apt-get install build-essential zlib1g-dev libffi-dev`. On macOS: `xcode-select --install`.

### "SyntaxError" in my .trump file

You made a mistake in your code. That happens. Even to the best people sometimes. Check:
- Are you using parentheses for function calls? `LOOK, FOLKS("hello")` not `LOOK, FOLKS "hello"`
- Are your phrases in ALL CAPS?
- Did you check [SYNTAX.md](SYNTAX.md) for the valid phrases?

### Something else is broken

Submit an issue on GitHub. We look at everything. Very carefully. The best response time in the business.

---

*For the full syntax reference, see [SYNTAX.md](SYNTAX.md).*

*For the main project overview, see [README.md](../README.md).*
