#!/usr/bin/env python3
"""Rebuild both RC2 tables in RFC 2268 from the decimal digits of pi.

No dependencies. Pi is computed here with Machin's formula in integer arithmetic.

The rule is the shuffle Rivest described for MD2's table (by email, quoted on
Cryptography Stack Exchange question 11935, 2014), except that every draw reads
exactly three digits:

    rand(n): read the next three digits as x (0..999).
             If x < n * floor(1000 / n), return x mod n. Otherwise discard x and read again.
    S = [0, 1, ..., 255]
    for i = 2 .. 256:  j = rand(i);  swap S[j] and S[i-1]

PITABLE (RFC 2268 section 2) starts at the first digit of pi, the leading 3.
The version Table[] (RFC 2268 section 6) runs the same loop four digits later, at "5926...".

Usage:  python3 reproduce.py               # compare with the tables printed below (copied from RFC 2268)
        python3 reproduce.py rfc2268.txt   # parse the tables from your own copy of the RFC instead
"""
import re
import sys

PITABLE_RFC = bytes.fromhex(
    "d978f9c419ddb5ed28e9fd794aa0d89dc67e37832b76538e624c6488448bfba2"
    "179a59f587b34f1361456d8d09817d32bd8f40eb86b77b0bf09521225c6b4e82"
    "54d66593ce60b21c7356c014a78cf1dc1275ca1f3bbee4d1423dd430a33cb626"
    "6fbf0eda4669075727f21d9bbc944303f811c7f690ef3ee706c3d52fc8661ed7"
    "08e8eade8052eef784aa72ac354d6a2a961ad2715a1549744b9fd05e0418a4ec"
    "c2e0416e0f51cbcc2491af50a1f47039997c3a8523b8b47afc02365b25559731"
    "2d5dfa98e38a92ae05df2910676cbac9d300e6cfe19ea82c6316013f58e289a9"
    "0d38341bab33ffb0bb480c5fb9b1cd2ec5f3db47e5a59c770aa62068fe7fc1ad")

VERSION_RFC = bytes.fromhex(
    "bd56eaf2a2f1ac2ab093d19c1b33fdd03004b6dc7ddf324bf7cb459b31bb215a"
    "419fe1d94a4d9edaa0682cc3275f80363eeefb951afecea834a913f0a63fd80c"
    "7824af2352c16717f56690e7e807b86048e61e53f392a4728c08156e860084fa"
    "f47f8a4219f6dbcd148d5012ba3c064eecb33511a1888e2b9499b77174d3e4bf"
    "3ade960ebc0aed77fc376b03798962c6d7c0d27c6a8b22a35b055d0275d561e3"
    "188f5551ad1f0b5e85e5c25763ca3d6cb4c5cc70b291590d4720c84f58e001e2"
    "1638c46f3b0f6546be7e2d7b82f940b51d73f8eb26c787972554b128aa989da5"
    "646d7ad4108144ef49d6ae2edd765c2fa71cc909699a83cf2939b9e94cff43ab")


def pi_digits(n):
    """First n decimal digits of pi as a string, leading '3' included."""
    def arctan_inv(x, one):
        total = term = one // x
        x2, k, sign = x * x, 1, -1
        while term:
            term //= x2
            total += sign * (term // (2 * k + 1))
            sign, k = -sign, k + 1
        return total
    one = 10 ** (n + 10)
    return str(4 * (4 * arctan_inv(5, one) - arctan_inv(239, one)))[:n]


def build(digits, width=lambda n: 3, discard=True):
    """Fisher-Yates shuffle of 0..255 driven by a digit string.

    width(n) is how many digits each draw reads (3 for RC2; 1, 2 or 3 for MD2).
    discard=False drops the rejection step (used only as a control)."""
    stream = iter(int(c) for c in digits)
    used = {"digits": 0, "discarded": 0}

    def rand(n):
        while True:
            w = width(n)
            x = 0
            for _ in range(w):
                x = x * 10 + next(stream)
            used["digits"] += w
            if not discard or x < n * (10 ** w // n):
                return x % n
            used["discarded"] += 1

    s = list(range(256))
    for i in range(2, 257):
        j = rand(i)
        s[j], s[i - 1] = s[i - 1], s[j]
    return bytes(s), used


def tables_from_rfc(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    def grab(after):
        part = text[text.index(after):]
        rows = re.findall(r"^\s+[0-9a-f]0: ((?:[0-9a-f]{2} ?){16})$", part, re.M)[:16]
        return bytes(int(h, 16) for h in " ".join(rows).split())
    return grab("PITABLE in hexadecimal"), grab("6. RC2 Algorithm Object Identifier")


def main():
    pitable, version = PITABLE_RFC, VERSION_RFC
    if len(sys.argv) > 1:
        pitable, version = tables_from_rfc(sys.argv[1])
    assert sorted(pitable) == list(range(256)) and sorted(version) == list(range(256))

    pi = pi_digits(3000)
    all_ok = True
    for name, target, start in (("PITABLE (RFC 2268 section 2)", pitable, 0),
                                ("Version table (RFC 2268 section 6)", version, 4)):
        built, used = build(pi[start:])
        same = sum(a == b for a, b in zip(built, target))
        print(f"{name}: starts at pi digit {start + 1} ('{pi[start:start + 4]}...'), "
              f"{used['digits']} digits read, {used['discarded']} draws discarded")
        print(f"  matches RFC byte-for-byte: {built == target} ({same}/256)")
        all_ok = all_ok and built == target

    # Controls (Table 1 of the write-up): near variants of the rule, compared with PITABLE.
    one = 10 ** 3010
    term, total, k = one, 0, 0
    while term:
        total, k = total + term, k + 1
        term //= k
    e = str(total)[:3000]

    def score(table):
        return sum(a == b for a, b in zip(table, pitable))

    def hex_first_occurrence():
        # hexadecimal digits of pi after the point, in pairs, keeping each byte the first time it appears
        bits = 4 * 4200 + 64
        one_b = 1 << bits
        def atan_inv(x):
            total = term = one_b // x
            x2, k, sign = x * x, 1, -1
            while term:
                term //= x2
                total += sign * (term // (2 * k + 1))
                sign, k = -sign, k + 1
            return total
        h = format((4 * (4 * atan_inv(5) - atan_inv(239))) >> 64, "x")[1:]
        seen = []
        for i in range(0, len(h) - 1, 2):
            b = int(h[i:i + 2], 16)
            if b not in seen:
                seen.append(b)
            if len(seen) == 256:
                break
        return seen

    md2 = lambda n: 1 if n <= 10 else (2 if n <= 100 else 3)
    print("controls (positions matching PITABLE, out of 256):")
    rows = [
        ("without the discard step", score(build(pi, discard=False)[0])),
        ("hexadecimal pi, first occurrences", score(hex_first_occurrence())),
        ("MD2's digit rule (1, 2 or 3 digits)", score(build(pi, width=md2)[0])),
        ("starting one digit later", score(build(pi[1:])[0])),
        ("digits of e", score(build(e)[0])),
    ]
    for label, value in rows:
        print(f"  {label:<36} {value:>3}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
