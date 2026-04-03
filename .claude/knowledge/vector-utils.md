# ベクトルユーティリティ — Park Skills 共通ナレッジ

Banner Park / 記事LP Park / Concept Park が共通で使うベクトル操作の標準コード。
各スキルはこのファイルを `Read` して使う。スキル内にコピペしない。

---

## 共通関数

```python
from google import genai
import os, subprocess, json, numpy as np

def _load_env(var):
    """環境変数をzshプロファイルから読み込む"""
    if not os.environ.get(var):
        try:
            r = subprocess.run(['zsh','-i','-c',f'echo ${var}'], capture_output=True, text=True, timeout=5)
            v = r.stdout.strip()
            if v: os.environ[var] = v
        except: pass

_load_env('GEMINI_API_KEY_1')
client = genai.Client(api_key=os.environ['GEMINI_API_KEY_1'])

def embed(text):
    """テキストをGemini Embeddingでベクトル化"""
    r = client.models.embed_content(model='gemini-embedding-001', contents=text)
    return r.embeddings[0].values

def cosine_sim(a, b):
    """コサイン類似度"""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

---

## hookVector 選択アルゴリズム（ベクトル多様性最大化）

N個のフック角度を、ベクトル空間上で最大限バラけるように自動選択:

```python
# strategy.json から hookVectors 読み込み
hook_pool = strategy['hookVectors']  # [{angle, text, vector}, ...]
n1_demand_vec = np.array([v['vector'] for v in all_vectors if v['category'] == 'layer_demand' and v['layer'] == primary_layer][0])

# N個を選択: 互いの sim <= 0.70（多様性）& N1需要 sim >= 0.45（刺さり度）
selected = []
pool = sorted(hook_pool, key=lambda h: -cosine_sim(np.array(h['vector']), n1_demand_vec))  # N1刺さり順

for h in pool:
    h_vec = np.array(h['vector'])
    if cosine_sim(h_vec, n1_demand_vec) < 0.45:
        continue
    too_similar = any(cosine_sim(h_vec, np.array(s['vector'])) > 0.70 for s in selected)
    if not too_similar:
        selected.append(h)
    if len(selected) >= target_count:
        break

# 足りない場合: salesCopy A/B や layerCommunication からフック候補を追加生成
```

**閾値基準**:
- N1需要との刺さり度: `sim >= 0.45`
- hookVector間の多様性: `sim <= 0.70`

---

## 4段階ベクトル品質ゲート

生成前にプロンプト/ヘッドラインの品質をベクトルで検証する。

### 準備

```python
# all_vectors.json 読み込み
all_vectors = json.load(open(f'research-park/output/{slug}/all_vectors.json'))
comp_vecs = [np.array(v['vector']) for v in all_vectors if v['category'] == 'competitor_message']
concept_vec = np.array(strategy['concept']['conceptVector'])
n1_demand_vec = np.array([v['vector'] for v in all_vectors if v['category'] == 'layer_demand' and v['layer'] == primary_layer][0])
```

### 検証コード

```python
# item_vecs = 検証対象のベクトルリスト [{index, vector, label}, ...]

gate_results = []
all_pass = True

# === 検証1: コンセプト一貫性（item × concept >= 0.50）===
for iv in item_vecs:
    sim = cosine_sim(iv['vector'], concept_vec)
    ok = sim >= 0.50
    if not ok: all_pass = False
    gate_results.append({'index': iv['index'], 'check': 'concept', 'sim': sim, 'pass': ok})

# === 検証2: 競合差別化（item × competitor_avg <= 0.55）===
for iv in item_vecs:
    avg = np.mean([cosine_sim(iv['vector'], c) for c in comp_vecs])
    ok = avg <= 0.55
    if not ok: all_pass = False
    gate_results.append({'index': iv['index'], 'check': 'competitor', 'sim': avg, 'pass': ok})

# === 検証3: アイテム間多様性（inter_item sim <= 0.70）===
for i in range(len(item_vecs)):
    for j in range(i+1, len(item_vecs)):
        sim = cosine_sim(item_vecs[i]['vector'], item_vecs[j]['vector'])
        if sim > 0.70:
            all_pass = False

# === 検証4: N1需要との刺さり度（参考値）===
for iv in item_vecs:
    sim = cosine_sim(iv['vector'], n1_demand_vec)
```

### 閾値基準

| 検証 | 条件 | 不合格時のアクション |
|---|---|---|
| コンセプト一貫性 | `sim >= 0.50` | ヘッドラインをコンセプトに寄せて再生成 |
| 競合差別化 | `avg <= 0.55` | フック角度変更 or 表現差別化 |
| アイテム間多様性 | `sim <= 0.70` | 類似ペアの片方のフック角度変更 |
| N1刺さり度 | 参考値 | 強制ではない。低い場合は注意喚起 |

**自動修正ループ**: 不合格 → 修正 → 再検証。3回トライしてFAILなら停止して報告。

---

## 事後検証（生成後）

生成したクリエイティブの実際のベクトルを検証:

```python
# actual_vec = 生成物のベクトル（embed()で取得）
# concept_vec = コンセプトベクトル

drift = cosine_sim(actual_vec, concept_vec)
# drift >= 0.50 → コンセプトに忠実
# drift < 0.50 → コンセプトからの逸脱あり → 再生成 or 微調整
```
