import torch
import pickle
import torch.nn as nn
import torch.optim as optim
import numpy as np
from scipy.spatial.distance import cosine

from knowledgegrap import Kg


class TransEDataPrep:
    def __init__(self, kg_instance):
        self.kg = kg_instance
        self.entities = sorted(list(self.kg.all_concepts.keys()))
        self.entity_to_idx = {ent_id: i for i, ent_id in enumerate(self.entities)}
        self.idx_to_entity = {i: ent_id for ent_id, i in self.entity_to_idx.items()}
        self.num_entities = len(self.entities)
        self.num_relations = 2

    def get_tensor_triples(self):
        triples = self.kg.get_triples()
        # FIX: Add '_' to catch the 4th value (weight) which we aren't using yet
        return torch.LongTensor([[self.entity_to_idx[h], r, self.entity_to_idx[t]] for h, r, t, _ in triples])




    #     self.kg = kg_instance
    #     self.entities = sorted(list(self.kg.all_concepts.keys()))
    #     self.entity_to_idx = {ent_id: i for i, ent_id in enumerate(self.entities)}
    #     self.idx_to_entity = {i: ent_id for ent_id, i in self.entity_to_idx.items()}
    #     self.num_entities = len(self.entities)
    #     self.num_relations = 2
    #
    # def get_tensor_triples(self):
    #     triples = self.kg.get_triples()
    #     return torch.LongTensor([[self.entity_to_idx[h], r, self.entity_to_idx[t]] for h, r, t in triples])


class TransE(nn.Module):
    def __init__(self, num_ent, num_rel, dim=64, margin=1.0):
        super(TransE, self).__init__()
        self.ent_embeddings = nn.Embedding(num_ent, dim)
        self.rel_embeddings = nn.Embedding(num_rel, dim)
        self.margin = margin
        nn.init.xavier_uniform_(self.ent_embeddings.weight)
        nn.init.xavier_uniform_(self.rel_embeddings.weight)

    def forward(self, h, r, t):
        h_e, r_e, t_e = self.ent_embeddings(h), self.rel_embeddings(r), self.ent_embeddings(t)
        return torch.norm(h_e + r_e - t_e, p=2, dim=1)



def train_knowledge_embeddings(dim=64, epochs=1000):

    prep = TransEDataPrep(Kg)
    triples = prep.get_tensor_triples()

    model = TransE(prep.num_entities, prep.num_relations, dim=dim)
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    print(f"--- Starting Training on {len(triples)} Triples ---")
    for epoch in range(epochs):
        with torch.no_grad():
            model.ent_embeddings.weight.data = torch.renorm(model.ent_embeddings.weight.data, p=2, dim=0, maxnorm=1.0)

        optimizer.zero_grad()
        h, r, t = triples[:, 0], triples[:, 1], triples[:, 2]
        pos_score = model(h, r, t)
        t_neg = torch.randint(0, prep.num_entities, t.shape)
        neg_score = model(h, r, t_neg)

        loss = torch.mean(torch.relu(model.margin + pos_score - neg_score))
        loss.backward()
        optimizer.step()

        if epoch % 200 == 0:
            print(f"Epoch {epoch:04d} | Loss: {loss.item():.4f}")

    final_vecs = model.ent_embeddings.weight.data.numpy()
    return {prep.idx_to_entity[i]: final_vecs[i] for i in range(prep.num_entities)}


if __name__ == "__main__":


    prep = TransEDataPrep(Kg)

    concept_vectors = train_knowledge_embeddings(dim=64)

    print("\n" + "=" * 30)
    print("ADVANCED KG VALIDATION")
    print("=" * 30)

    # TEST A: RELATIONAL CLUSTERING (BFS vs DFS)
    sim_bfs_dfs = 1 - cosine(concept_vectors[102], concept_vectors[103])
    print(f"1. Semantic Similarity (BFS/DFS): {sim_bfs_dfs:.4f} (High is good)")

    # TEST B: CROSS-DOMAIN DISTANCE (BFS vs Modular Arithmetic)
    sim_bfs_math = 1 - cosine(concept_vectors[102], concept_vectors[1103])
    print(f"2. Domain Separation (BFS/Math):  {sim_bfs_math:.4f} (Low is good)")


    # TEST C: PREDICTIVE RANKING (The 'Hidden' Validation)
    # Pick a real triple: (101, 1, 102) -> Representation is Prereq for BFS
    # We check how 'close' the model thinks this is compared to 100 random concepts

    def calculate_rank(head_id, rel_idx, tail_id, vectors, all_ids):
        h_vec = vectors[head_id]
        t_vec = vectors[tail_id]
        # In a real run, you'd pull the actual trained relation vector:
        # rel_vec = model.rel_embeddings.weight[rel_idx].detach().numpy()

        # Simplified validation: Is the distance (h -> t) smaller than (h -> random)?
        true_dist = np.linalg.norm(h_vec - t_vec)

        better_than = 0
        for random_id in all_ids:
            if random_id == tail_id: continue
            random_dist = np.linalg.norm(h_vec - vectors[random_id])
            if random_dist < true_dist:
                better_than += 1
        return better_than + 1


    all_ids = list(concept_vectors.keys())
    rank = calculate_rank(101, 1, 102, concept_vectors, all_ids)
    print(f"3. Prerequisite Rank: {rank}/{len(all_ids)} (Lower is better)")

    if rank < 10:
        print("\nStatus: EXCELLENT. The model understands the specific links.")
    else:
        print("\nStatus: OK. Model knows clusters, but needs more epochs for specific links.")
    import pandas as pd

    # ... (your existing training code) ...
    concept_vectors = train_knowledge_embeddings(dim=64)

    # 1. Convert dictionary to a DataFrame
    # Keys are IDs, values are the numpy arrays
    df = pd.DataFrame.from_dict(concept_vectors, orient='index')

    # 2. Rename the index to 'entity_id' for clarity
    df.index.name = 'entity_id'

    # 1️⃣ Save as .npy
    all_vectors = np.array(list(concept_vectors.values()))
    np.save('concept_embeddings.npy', all_vectors)
    print("✅ Saved embeddings to 'concept_embeddings.npy'")

    # 2️⃣ Save as .pkl (dictionary format, preserves IDs)
    with open('concept_embeddings.pkl', 'wb') as f:
        pickle.dump(concept_vectors, f)
    print("✅ Saved embeddings to 'concept_embeddings.pkl'")

    # 3️⃣ CSV is already saved (optional)
    df.to_csv('concept_embeddings.csv')
    print("✅ Saved embeddings to 'concept_embeddings.csv'")

    print(f"\nSuccessfully saved {len(df)} embeddings to 'concept_embeddings.csv'")
