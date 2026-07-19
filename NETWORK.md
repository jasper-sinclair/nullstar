# Nullstar NNUE network

Nullstar links its default NNUE directly into the executable as
`src/net.cpp`. No external network file is required at runtime.

## Active development network

Nullstar 003 embeds the 768x256 **Set 006** network trained by Jasper Sinclair
in the Kobra/Cobra training line. The archived development set is retained
locally as `TRAINING 227 768-256 SET 006`; its multi-gigabyte source datasets
and generated checkpoints are not suitable for the source repository.

The testing archive of Nullstar 002 and the current Nullstar 003 source contain
identical 394,754-byte quantized network data. Nullstar 003 regenerates the C++
representation with the repository's cleaned, reproducible embedding tool.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Quantized `network.bin` | 394,754 | `30A74951A897E696A5156BC9E192771DB99FE5754A6431D7EA2D562003224CE6` |
| Generated `src/net.cpp` | 2,492,329 | `3E08DD56DA2D5C70B0C406211A74F1058391B18726C4E9C4CCFAE31D07630363` |
| Archived `best_model.pt` | 792,025 | `B495A39E6238F4BD97D1FCCB7949D5C9086C7A3F7E1ECEC28F9418B6A279D903` |
| Archived `config.json` | 1,349 | `B34801389203B02D3445DFB6A8D67030C0B746347DA528D4CE932564B5EF454A` |

The generated C++ array was independently decoded and verified byte-for-byte
against the quantized network. The archived configuration is preserved as
`training/configs/nullstar-002-set006.json`.

## Rebuilding or replacing the network

The full source workflow is documented in `training/README.md`:

1. generate `training.txt` with Nullstar self-play;
2. validate, shuffle, and convert it to the sparse format;
3. train and export `network.bin`;
4. use `tools/embed_file` to regenerate `src/net.cpp`;
5. rebuild and benchmark the engine;
6. establish strength with controlled paired match testing.

Exact retraining of Set 006 requires its original 38 GB archived dataset.
That archive remains development material rather than a Git dependency; the
quantized model itself is completely preserved by tracked `src/net.cpp`.
