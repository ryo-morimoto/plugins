# tellman-naming

> **検証中（experimental）です。** より良いスコープに組み替える可能性が高く、名前・構成は、予告なく変わります。

名前を付けるか、何と呼ぶか、既存の名前を変えるべきかを、Zach Tellman の *Elements of Clojure*（2019）の考え方で判断する skill を 1 つ持つ plugin です。一般的な助言（説明的な名前、小さな関数、抽出して名付ける）と食い違うところでは、この基準に従い、食い違ったことを 1 行で言います。

## 構成

| 部品 | 内容 |
| --- | --- |
| `skills/tellman-naming/SKILL.md` | 目次。作業の種類ごとに読むファイルを示す |
| `core/` | 名前を作らない判断、既存の名前の判定、束縛・関数・境界、用語、例、答え方 |
| `packs/` | 言語ごとの既定（Clojure、TypeScript、Rust）。足し方は `packs/README.md` |

本の要約と、そこから引いた判断の手順です。本文の引用はしていません。

## インストール

```
/plugin install tellman-naming --marketplace ryo-morimoto/plugins
```

claude.ai に同じ skill を上げている場合は、そちらを外してください。同じ名前の skill が 2 つ並びます。
