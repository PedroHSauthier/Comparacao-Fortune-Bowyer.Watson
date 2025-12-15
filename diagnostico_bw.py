
import random
import numpy as np
import sys
import os

# Adiciona o diretório atual ao path para importar o módulo
sys.path.append(os.getcwd())

try:
    from Bowyer.bowyer_watson_cython import BowyerWatsonCython
except ImportError as e:
    print(f"Erro ao importar: {e}")
    exit(1)

def main():
    print("--- Diagnóstico Bowyer-Watson ---")
    
    # Gera 10 pontos simples
    points = [[random.uniform(0, 100), random.uniform(0, 100)] for _ in range(10)]
    print(f"Pontos gerados (primeiros 3): {points[:3]}")

    bw = BowyerWatsonCython(points)
    bw.run()

    print(f"\nMétricas:")
    print(f"Delaunay Triangles: {bw.metrics['delaunay_triangles']}")
    print(f"Voronoi Edges: {bw.metrics['voronoi_edges_created']}")

    print("\nArestas Voronoi (Amostra):")
    if not bw.voronoi_edges:
        print("NENHUMA ARESTA ENCONTRADA!")
    else:
        for i, (p1, p2) in enumerate(bw.voronoi_edges):
            print(f"  Aresta {i}: ({p1.x:.2f}, {p1.y:.2f}) -> ({p2.x:.2f}, {p2.y:.2f})")
            if i >= 5:
                print("  ...")
                break
    
    # Verifica limites
    if bw.voronoi_edges:
        min_x = min(min(e[0].x, e[1].x) for e in bw.voronoi_edges)
        max_x = max(max(e[0].x, e[1].x) for e in bw.voronoi_edges)
        min_y = min(min(e[0].y, e[1].y) for e in bw.voronoi_edges)
        max_y = max(max(e[0].y, e[1].y) for e in bw.voronoi_edges)
        print(f"\nLimites das arestas Voronoi:")
        print(f"  X: {min_x:.2f} a {max_x:.2f}")
        print(f"  Y: {min_y:.2f} a {max_y:.2f}")
        
        # Verifica se está muito longe dos pontos (0-100)
        if min_x < -500 or max_x > 500 or min_y < -500 or max_y > 500:
            print("\n[ALERTA] As coordenadas parecem estar fora da escala esperada (0-100)!")

if __name__ == "__main__":
    main()
