# RC2's π tables, rebuilt from the digits of π

[![reproduce](https://github.com/khalid-hamadeh/rc2-pi-tables/actions/workflows/reproduce.yml/badge.svg)](https://github.com/khalid-hamadeh/rc2-pi-tables/actions/workflows/reproduce.yml)

RFC 2268 prints two 256-byte permutations for Ron Rivest's RC2 cipher. It says PITABLE is "based on the digits of PI" but gives no method, and it gives the version table in section 6 no origin at all. Several implementations still carry the comment from the 1996 leak: "probably derived somehow from pi".

Both tables are reproduced exactly by one rule: the Fisher–Yates shuffle, with the decimal digits of π as the source of randomness, reading **exactly three digits per draw**.

```
digits: decimal digits of pi, leading 3 included: 3 1 4 1 5 9 2 6 5 3 ...

rand(n):  read the next three digits as x (0..999)
          if x < n * floor(1000 / n): return x mod n
          otherwise discard x and read three more

S = [0, 1, ..., 255]
for i = 2 .. 256:
    j = rand(i)
    swap S[j], S[i-1]
```

| Table | Starts at | Digits read | Draws discarded | Matches RFC 2268 |
|---|---|---|---|---|
| PITABLE (§2) | the leading 3 (`3141…`) | 828 | 21 | 256 / 256 |
| Version table (§6) | the fifth digit (`5926…`) | 828 | 21 | 256 / 256 |

The shuffle is the one Rivest confirmed for MD2's table in 2014 ([Cryptography Stack Exchange](https://crypto.stackexchange.com/questions/11935)). MD2 reads one, two or three digits per draw depending on n; RC2 always reads three. MD2's exact rule applied to RC2 matches 1 of 256 entries, which may be why the two were never connected.

## Run it

```
python3 reproduce.py               # compare with the tables in this repository
python3 reproduce.py rfc2268.txt   # or with your own copy of RFC 2268
```

No dependencies. The script computes π itself (Machin's formula, integer arithmetic), runs the controls from Table 1 of the write-up, and exits non-zero if either table fails to match. The badge above runs it on every push, including against a fresh download of RFC 2268.

```
PITABLE (RFC 2268 section 2): starts at pi digit 1 ('3141...'), 828 digits read, 21 draws discarded
  matches RFC byte-for-byte: True (256/256)
Version table (RFC 2268 section 6): starts at pi digit 5 ('5926...'), 828 digits read, 21 draws discarded
  matches RFC byte-for-byte: True (256/256)
controls (positions matching PITABLE, out of 256):
  without the discard step              29
  hexadecimal pi, first occurrences      2
  MD2's digit rule (1, 2 or 3 digits)    1
  starting one digit later               1
  digits of e                            0
```

## Files

- `reproduce.py`: the construction, the comparison and the controls
- `tables/`: both tables as printed in RFC 2268, in hexadecimal (`.hex`) and decimal (`.txt`)
- `CITATION.cff`: citation metadata

## Write-up

The history of the cipher, an animated walkthrough of the shuffle, the alternatives that were ruled out, and the search for earlier work: [How RC2's π table was made](https://khalidhamadeh.com/writing/rc2-pi-table).

## Notes

What this establishes: the rule reproduces both published tables exactly. What it strongly suggests, but cannot prove: that this is how they were originally generated. What it cannot tell us: how Rivest arrived at the rule, or whether he considered alternatives.

RC2 is long deprecated, and this result has no bearing on its security. Rivest presumably always knew the method; the claim is only that we found no earlier publication of it. One may exist in a source we did not reach. If you know of one, please open an issue and it will be credited.

The rule was found by an AI agent (Anthropic's Claude) working on a list of long-unanswered questions, and confirmed by an independent implementation (OpenAI's Codex). The check above does not depend on trusting either.

Khalid Hamadeh, October 2026. MIT licence.
