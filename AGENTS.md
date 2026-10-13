# Maintenance / 维护约定

- Core: `src/prefixfold/{cache,attention,cli}.py`; evidence: `results/`; protocols: `research/` and `configs/`.
  核心代码、原始证据与实验协议分开维护。
- Install: `uv sync --frozen --group bench`; demo: `uv run prefixfold demo`.
  使用锁定的隔离环境，默认示例离线运行。
- Check: `make check`; test: `make test`; benchmark: `make benchmark`; build: `make build`.
  修改后运行受影响的检查。
- Keep README.md / README_zh.md and docs/en / docs/zh semantically aligned.
  公共说明、API 和核心注释提供中英双语；配置键统一英文。
- Preserve all valid benchmark samples, failures, targets, provenance and source hashes. Generated tables derive from raw JSON.
  不删除不利结果，不把理论、目标或未运行状态写成实测。
- Do not publish secrets, private paths, personal email, model weights or unrelated files. Do not change global identity, rewrite history, buy services, or deploy without explicit authorization.
  未获明确授权不得推送、公开发布、创建付费资源或部署；本地提交仅暂存相关文件。
- A change is complete when behavior, tests, bilingual docs, source-linked acceptance and relevant benchmarks agree.
  完成条件：实现、测试、双语文档、验收证据与必要实验一致。

- Before each new commit, run `make precommit-identity`; it resolves both author and committer using Git, including environment overrides. Use the already verified repository-local GitHub privacy identity, and never print identity values in check output. / 每次新提交前运行该命令，检查包括环境覆盖在内的实际作者与提交者；沿用已核实的仓库局部隐私身份，检查不回显身份值。
- After committing and before pushing, run the full `scripts/audit.py` and review the new commits. The identity preflight is only prevention; it does not replace historical audit. A known history privacy finding remains unresolved until separately addressed within authorized constraints. Do not hide it by shallow checkout, exemptions or rewriting published history. / 提交后、推送前执行完整审查并核对新增提交；身份预检仅用于防复发，不能替代历史审查。已知历史隐私发现仍未解决，不得用浅克隆、豁免或改写已发布历史隐藏。
