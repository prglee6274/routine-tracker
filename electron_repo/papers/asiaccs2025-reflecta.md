# REFLECTA: Reflection-based Scalable and Semantic Scripting Language Fuzzing

**Authors:** Chibin Zhang, Gwangmu Lee, Qiang Liu, Mathias Payer (all EPFL, HexHive)
**Venue / Year:** ACM AsiaCCS 2025 (Hanoi, Vietnam, 25–29 August 2025), Cycle 1 · 16 pages
**Links:** [ACM DOI 10.1145/3708821.3710818](https://doi.org/10.1145/3708821.3710818) · [PDF (author-hosted, HexHive)](https://hexhive.epfl.ch/publications/files/25AsiaCCS.pdf) · [Artifact](https://github.com/HexHive/Reflecta)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** It is the strongest existing demonstration that a fuzzer can discover a scripting engine's *entire reachable API surface at runtime, from zero specification*, using reflection alone — which is exactly the capability an Electron auditor needs, because an Electron app's bridge API (`contextBridge`, `ipcRenderer` channels) is per-application, undocumented, and has no grammar, no Web IDL and no corpus anywhere.

> **한 줄 요약 (KO):** 문법·타입 명세를 전혀 주지 않고 **리플렉션만으로** 스크립팅 엔진의 내장 객체/메서드 표면을 런타임에 열거해 타입 정확한 프로그램을 생성하는 언어 범용 퍼저. 4개 언어·6개 엔진(CPython, MicroPython, CRuby, MRuby, PHP, V8)에서 의미적 정확도 평균 62.3%(Nautilus 35.7%, PolyGlot 20.2%)를 달성하고 신규 버그 25개를 찾았다. **"명세가 없는 API 표면을 어떻게 찾을 것인가"** 라는 문제를 정면으로 다룬다는 점에서 Electron preload/IPC 표면 감사와 직결된다.

---

## 1. Problem, Gap & Hypothesis

Scripting-language execution engines (V8, CPython, PHP, CRuby …) present a large attack surface: bugs inside the engine break the memory-safety and sandboxing guarantees the language advertises, enabling sandbox escape and arbitrary code execution on the host. Fuzzing is the established response, but the paper argues existing fuzzers fail on two axes simultaneously:

- **Scalability.** Engine-specific fuzzers do not transfer. Fuzzilli (~45K LoC) is JavaScript-only and centred on JIT bugs; grammar-based fuzzers need a hand-written grammar per language that goes stale as libraries evolve. Alternative implementations of the *same* language (CPython vs MicroPython, CRuby vs MRuby) each diverge, so even a per-language grammar under-specifies some engines.
- **Semantic correctness.** Syntax-only generation passes the parser and then dies at the first type check. The manual fix — annotating types by hand — does not scale: the paper counts Fuzzilli spending **1,182 LoC purely on type annotations for built-in objects and functions**, plus several hundred lines of per-engine profile. And static annotation is *insufficient in principle*, because in a dynamically typed language the valid semantics of a program are only determined at runtime.

**Hypothesis:** reflection — the introspection facility every modern scripting language already ships (`Object.constants`, `.methods()`, `.class()`, `.arity()` in the Ruby example of Fig. 1) — is a *universal* channel for obtaining precise, runtime-accurate semantic information. If the fuzzer queries the engine itself for what exists and what types it takes, it needs no grammar beyond a minimal invariant core syntax, and it automatically tracks whatever libraries the particular engine build actually contains.

> **(KO)** 핵심 통찰은 "명세를 사람이 쓰지 말고 **대상에게 물어보라**"는 것. 정적 주석은 (a) 유지보수가 안 되고 (b) 동적 타입 언어에서는 원리적으로 불완전하다는 두 가지 이유로 기각된다. 이 두 번째 논거가 Electron 논문에 그대로 재사용 가능하다 — ipcMain 핸들러의 유효 인자 타입은 정적으로 알 수 없다.

## 2. Methodology

Three components:

1. **Program generation via reflective enumeration.** REFLECTA starts from a minimal, invariable core syntax and uses reflection to enumerate built-in language features — built-in objects, functions and modules — then emits language-feature-rich programs over whatever it found. Because the enumeration happens inside the target process, it adapts automatically to the engine build.
2. **Type-aware program mutation.** For each discovered method it deduces a type-correct signature at runtime (an ε-greedy explore/exploit scheme over candidate signatures), so mutations call methods with arguments of the right type instead of guessing.
3. **Type-enhanced corpus feedback.** The corpus is scheduled with type information as an additional signal, so programs containing rare types or attributes get more energy than programs made of common literals (strings, integers).

Deliberate design exclusion, and it matters for how the paper should be cited: **REFLECTA does not generate control-flow structure** (loops, conditionals, function definitions) at all, on the grounds that control flow is orthogonal to what reflection tells you and mostly produces dead code.

> **(KO)** 설계 3단계: ① 리플렉션으로 API 표면 열거 → ② 런타임 시그니처 추론(ε-greedy)으로 타입 정확한 변이 → ③ 희귀 타입 우선 코퍼스 스케줄링. **제어 흐름을 일부러 생성하지 않는다**는 점이 이 논문의 성격을 결정한다 — JIT 버그가 아니라 **표준 라이브러리/바인딩 표면 버그**를 노리는 퍼저다.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

- **Targets:** 6 engines across 4 languages — CRuby, MRuby, CPython, MicroPython, PHP, V8. Languages chosen as the top four scripting languages in the Stack Overflow 2023 Developer Survey; two of the four have a second implementation deliberately included to test self-adaptation.
- **Sanitizers:** all targets built with AddressSanitizer except Ruby (ASan build crashes). Edge coverage measured offline on a separately built SanitizerCoverage binary. Persistent drivers reused/created for all targets except Nautilus, which uses its own incompatible forkserver.
- **Baselines:** Nautilus, PolyGlot, Fuzzilli (JS only), plus a best-effort comparison against PyRTFuzz (CPython-only; the authors could not reproduce it on Python 3.12 and fall back to Python 3.9 in Appendices D–E). SoFi could not be compared — not open-sourced.
- **Specification budget (Table 3), the paper's cleanest single result:** REFLECTA uses **83–91 LoC of grammar and 0 symbols** per language. Nautilus needs 8,719 grammar rules + 8,655 symbols for PHP alone (972 + 852 for JavaScript, 1,176 + 1,142 for Ruby, 637 + 412 for Python); Fuzzilli 881 + \*1,181 for JavaScript; PyRTFuzz \*1,205 symbols for Python.
- **Configuration:** cluster nodes with a 16-core Intel Xeon 5218 and 64 GB RAM, hyper-threading disabled, each fuzzing instance pinned to one core with `cpuset`. Comparative experiments: **24 hours × 8 repetitions per fuzzer–target pair**, 95% confidence intervals shaded in the coverage plots. Bug-finding campaign: **three months**, but *all bugs were found within 24 hours*.
- **Measured:** (RQ1) semantic correctness rate = correct executions / total executions; (RQ2) edge coverage over 24 h, including an ablation `REFLECTA-Sem` without type-correct mutation; (RQ3) new bugs in real engines; (RQ4) effort to add a new target (SpiderMonkey, Appendix C).

> **(KO)** 실험 설계에서 논문에 인용할 가치가 가장 큰 숫자는 **명세 비용**이다: REFLECTA 83–91 LoC / 심볼 0개 vs Nautilus PHP 8,719 + 8,655. 24시간 × 8회 반복, 95% 신뢰구간이라는 설정은 퍼징 평가 관행상 "제대로 한" 쪽에 속한다(6절의 SoFi 대비 참고).

## 4. Results / Key Findings — concrete numbers

**Semantic correctness (Table 4, correct/total over a 24 h campaign):**

| Target | Nautilus | PolyGlot | Fuzzilli | REFLECTA |
|---|---|---|---|---|
| Ruby | 34.8% (1116/3207) | 19.8% (421/2127) | — | **61.0%** |
| MRuby | 34.7% (821/2364) | 25.7% (397/1544) | — | **62.5%** |
| CPython | 28.3% (711/2513) | 14.0% (158/1127) | — | **53.1%** |
| MicroPython | 36.6% (1430/3907) | 22.3% (131/587) | — | **62.1%** |
| PHP | 40.1% (1966/4903) | 29.7% (1323/4455) | — | **70.8%** |
| V8 | 39.3% (419/1066) | 9.8% (291/2973) | **67.7%** | 64.2% |
| **Average** | **35.7%** | **20.2%** | 67.7% (JS only) | **62.3%** |

- Aggregate improvement: **1.74× correctness over Nautilus, 3.35× over PolyGlot**; **1.63× / 2.21× edge coverage** respectively. On V8, REFLECTA reaches 64.2% against Fuzzilli's 67.7% *with zero semantic annotations* against Fuzzilli's 1,181 LoC of them.
- Failure analysis of the remaining ~38%: requirements beyond type correctness — stateful invocation, call ordering, string arguments with a required format (e.g. XML). CPython is the weakest target (53.1%) because its large standard library slows signature deduction, and because Python is more strongly typed than Ruby/PHP/JS so implicit coercion rescues fewer calls.
- **Bugs (Table 6): 25 unique previously-unknown bugs, all confirmed by developers, 16 fixed** — 8 in MRuby, 14 in MicroPython, 3 in PHP. Types: null-deref (×10), heap-buffer-overflow (×3), heap-UAF (×3), global-buffer-overflow (×5), segfault (×2), stack-overflow (×1). Crash sites include `mrb_vm_exec`, `mrb_struct_to_h`, `ary_rotate_bang`, `mpz_as_bytes`, `mp_obj_class_lookup`, `zend_hash_clean`, `zif_func_num_args`. Of the baselines only Nautilus found new bugs (3 in MicroPython) and **all of them were a subset of REFLECTA's**.
- **REFLECTA found zero new bugs in V8**, and the paper says plainly why: recent V8 bugs live in the JIT optimisation pipeline, which needs loops to make code hot, and REFLECTA generates no control flow. "REFLECTA primarily finds bugs in standard libraries."
- Case study (Fig. 9): a 4-line MRuby stack overflow — `it = {}.lazy()`, `it.args=(it)` (circular self-reference), `fmap = it.filter_map()`, `fmap.count()`. Nautilus and PolyGlot missed it purely because `filter_map` and `args=` were absent from the hand-written grammar and the seed corpus. **Under-specification of the API surface, not weak search, is what hid the bug.**
- Ablation: `REFLECTA-Sem` (no type-correct mutation) is consistently below full REFLECTA, and REFLECTA's margin over Nautilus is *larger* on the reference implementations (CRuby, CPython) than on the small ones (MRuby, MicroPython), because the reference builds have bigger standard libraries that a pre-engineered grammar under-covers.
- Generality claim: SpiderMonkey integration demonstrated in Appendix C; Lua, Perl and R verified to support reflection and to be supportable "as-is with only minor engineering costs".

> **(KO)** 인용에 쓸 핵심 수치: 평균 62.3% vs 35.7%/20.2%, 커버리지 1.63×/2.21×, 신규 버그 25개(16개 수정). **가장 중요한 음성 결과는 "V8에서 신규 버그 0건"** — 제어 흐름을 생성하지 않아 JIT 버그를 못 찾는다는 자백이며, 이것이 이 논문을 Fuzzilli 계열(엔진 내부)이 아니라 Favocado/COOPER 계열(호스트 노출 API 표면)로 분류해야 하는 근거다.

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> Recent work on scripting-engine testing has moved away from hand-written specifications. REFLECTA (Zhang et al., AsiaCCS 2025) shows that a fuzzer can recover an engine's built-in object, function and module surface *at runtime through reflection alone*, reducing the per-language specification from thousands of grammar rules and symbols — 8,719 rules and 8,655 symbols for PHP in Nautilus, 1,181 lines of type annotation for JavaScript in Fuzzilli — to 83–91 lines of invariant core syntax and no symbol list at all. Across six engines for four languages it raises semantic correctness from 35.7% (Nautilus) and 20.2% (PolyGlot) to 62.3%, and discovers 25 previously unknown bugs in MRuby, MicroPython and PHP.
> Its central negative result is as informative as its positive one: REFLECTA found no new bugs in V8, because it deliberately generates no control flow and therefore cannot reach the JIT optimisation pipeline where most recent V8 bugs live. It is a fuzzer of *exposed API surface*, not of engine internals.
> That is precisely the surface an Electron application adds. Where REFLECTA reflects over an engine's built-ins, an Electron renderer faces an *application-defined* bridge — objects injected by a preload script through `contextBridge` and string-keyed channels registered with `ipcMain.handle` — for which no grammar, no Web IDL and no seed corpus exists, and whose valid argument types are likewise only determined at runtime.

**(KO) 위치 잡기 — 취약점 *발견* 논문 대비:** 이 논문은 **동기(motivation)이자 방법론적 직계 조상**이지 방어 기법 대비 사례가 아니다. 세 가지로 쓸 수 있다. ① *"명세 없는 표면을 어떻게 퍼징하는가"* 라는 문제가 이미 top-tier에서 풀린 문제임을 보여 준다 — 즉 Electron IPC 표면에 같은 질문을 던지는 것이 정당하다. ② **남겨 둔 공백이 명확하다**: REFLECTA의 리플렉션 대상은 *언어 런타임이 제공하는* 표면이고, Electron의 위험한 표면은 *애플리케이션이 직접 추가한* 표면이다. `contextBridge.exposeInMainWorld`로 주입된 객체는 렌더러에서 리플렉션으로 열거가 **가능**하지만, `ipcRenderer.invoke('channel', ...)`의 채널 이름 집합은 리플렉션으로 열거가 **불가능**하다(문자열 키). 이 비대칭이 논문의 연구 질문이 된다. ③ 오라클 공백: REFLECTA의 오라클은 ASan 크래시뿐이며, Electron에서 문제되는 것은 메모리 오염이 아니라 **권한 상승**(파일 쓰기, 프로세스 생성)이라 오라클 자체를 새로 정의해야 한다. 09-18 NDSS'26 항목이 제기한 "ground-truth invariant가 없다"는 공백과 정확히 같은 지점이다.

## 6. Caveats / what I could not confirm from the text

- **Grounding:** full text read from the author-hosted PDF. Read closely: abstract, §1 Introduction, Table 1, §6 Evaluation (setup, Table 3, §6.2 + Table 4, §6.3 opening, §6.4 + Table 6 + Fig. 9), §7 Limitation and Discussion, §8 Related Work, §9. **Not** read line-by-line: §2 Background, §3 Motivation and Requirements, §4 Design (4.1–4.3 internals), §5 Implementation, and Appendices A–G. No coverage figure is quoted as a raw edge count because Figure 6 gives coverage only as plots; the 1.63×/2.21× aggregates are the paper's own stated numbers.
- **Electron is never mentioned.** Neither are Node.js, desktop applications, or embedders of any kind. V8 is fuzzed as a standalone engine (`d8`-style driver), not as an embedded engine with host-injected objects. Every sentence in this note about `contextBridge`/`ipcMain` is *my* extrapolation, not the paper's claim — do not cite it as Electron evidence.
- The comparison against PyRTFuzz is explicitly "best effort": the authors hit compatibility problems generating API specifications for Python 3.12 and fell back to Python 3.9 using PyRTFuzz's own reported bugs and replication package. Treat any PyRTFuzz-vs-REFLECTA claim as weaker than the Nautilus/PolyGlot/Fuzzilli comparisons.
- SoFi (CCS'21), listed in Table 1 as the other reflection-using semantic-aware fuzzer, **could not be compared at all** because it is not available as open source (the authors note prior work reports the same). So the REFLECTA-vs-SoFi delta is unmeasured in either direction.
- Ruby is built **without** AddressSanitizer (ASan executable crashes), so the bug counts for CRuby are not comparable in sensitivity to the other targets. Note that all 25 bugs are in MRuby/MicroPython/PHP and none in CRuby, CPython or V8.
- Whether reflection can enumerate host-injected objects in a real embedder is not tested anywhere in the paper; the closest statement is §7's speculation that reflection could also explore "deleting object attributes or redefining methods at runtime".
