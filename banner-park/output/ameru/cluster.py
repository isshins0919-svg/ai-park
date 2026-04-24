#!/usr/bin/env python3
"""Phase 3.1: 画像ベクトルで階層クラスタリング
   入力: reference/all_vectors.json
   出力: reference/clusters.json (各refに cluster_id 付加)
"""
import json
import numpy as np
from pathlib import Path
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist

ROOT = Path(__file__).parent
IN_JSON = ROOT / "reference" / "all_vectors.json"
OUT_JSON = ROOT / "reference" / "clusters.json"

refs = json.loads(IN_JSON.read_text())
ids = [r['id'] for r in refs]
image_vecs = np.array([r['image_vec'] for r in refs])
multi_vecs = np.array([r['multimodal_vec'] for r in refs])

def cosine_distances(vecs):
    # コサイン距離 = 1 - コサイン類似度
    norm = np.linalg.norm(vecs, axis=1, keepdims=True)
    vecs_n = vecs / norm
    sim = vecs_n @ vecs_n.T
    return 1 - sim

def hcluster(vecs, n_clusters=3):
    dist = cosine_distances(vecs)
    # condensed distance (1次元)
    cond = dist[np.triu_indices(len(vecs), k=1)]
    Z = linkage(cond, method='average')
    labels = fcluster(Z, t=n_clusters, criterion='maxclust')
    return labels, dist

# image_vec でクラスタリング
labels_img, dist_img = hcluster(image_vecs, n_clusters=3)
# multimodal_vec でもクラスタリング（比較用）
labels_multi, dist_multi = hcluster(multi_vecs, n_clusters=3)

# コサイン類似度行列（参考用、丸め表示）
def sim_matrix(vecs):
    norm = np.linalg.norm(vecs, axis=1, keepdims=True)
    vecs_n = vecs / norm
    return (vecs_n @ vecs_n.T)

sim_img = sim_matrix(image_vecs)

print("=== 画像ベクトル 類似度行列（10×10） ===")
print("      ", " ".join(f"{i+1:>5}" for i in range(len(ids))))
for i, vid in enumerate(ids):
    label_short = vid[:15]
    print(f"{i+1:>2} {label_short:<15}", " ".join(f"{sim_img[i][j]:>5.2f}" for j in range(len(ids))))

print("\n=== クラスタ割当 ===")
print(f"{'ID':<22} | {'image_cluster':<14} | {'multi_cluster':<14}")
print("-" * 60)
for i, ref in enumerate(refs):
    ref['cluster_image'] = int(labels_img[i])
    ref['cluster_multi'] = int(labels_multi[i])
    print(f"{ref['id']:<22} | img: {ref['cluster_image']:<9} | multi: {ref['cluster_multi']}")

# クラスタごとに集約
print("\n=== 画像クラスタの中身 ===")
for c in sorted(set(labels_img)):
    members = [r for r in refs if r['cluster_image'] == c]
    print(f"\n-- 画像クラスタ {c} ({len(members)}件) --")
    for m in members:
        print(f"  {m['src']:<28} | {m['copy'][:40]}")

print("\n=== マルチモーダルクラスタの中身 ===")
for c in sorted(set(labels_multi)):
    members = [r for r in refs if r['cluster_multi'] == c]
    print(f"\n-- multimodalクラスタ {c} ({len(members)}件) --")
    for m in members:
        print(f"  {m['src']:<28} | {m['copy'][:40]}")

# ベクトルは削ってメタだけ保存（軽量化）
for r in refs:
    for k in ['image_vec', 'text_vec', 'multimodal_vec']:
        r.pop(k, None)

OUT_JSON.write_text(json.dumps({
    "refs": refs,
    "similarity_matrix_image": sim_img.tolist(),
    "ids": ids,
}, ensure_ascii=False, indent=2))
print(f"\nsaved: {OUT_JSON}")
