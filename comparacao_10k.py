"""
Script para comparar a performance dos algoritmos de Voronoi com 8.000 pontos:
- Algoritmo de Fortune (SciPy)
- Algoritmo de Bowyer-Watson (Cython)

Executa 5 vezes e utiliza os dados da última execução.
"""

import time
import tracemalloc
import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d

# Importa a implementação otimizada
try:
    from Bowyer.bowyer_watson_cython import BowyerWatsonCython
except ImportError:
    print("ERRO: Módulo 'Bowyer.bowyer_watson_cython' não encontrado ou incompatível.")
    print("Certifique-se de que a extensão Cython foi compilada corretamente.")
    exit(1)

def run_scipy_fortune(points):
    """ Executa o algoritmo de Voronoi do SciPy e coleta métricas. """
    metrics = {}
    tracemalloc.start()
    start_time = time.perf_counter()
    
    voronoi = Voronoi(points)
    
    metrics["execution_time_sec"] = time.perf_counter() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics["peak_memory_mb"] = peak_mem / (1024 * 1024)
    metrics["voronoi_vertices"] = len(voronoi.vertices)
    metrics["voronoi_edges"] = len(voronoi.ridge_points)
    return metrics, voronoi

def run_bowyer_watson_cython(points):
    """ Executa implementação do Bowyer-Watson com Cython e coleta métricas. """
    tracemalloc.start()
    start_time = time.perf_counter()

    bw_generator = BowyerWatsonCython(points)
    bw_generator.run()
    metrics = bw_generator.metrics

    metrics["execution_time_sec"] = time.perf_counter() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics["peak_memory_mb"] = peak_mem / (1024 * 1024)
    
    return metrics, bw_generator

def main():
    # Configuração
    N_POINTS = 10000
    N_RUNS = 5
    
    print(f"Iniciando teste de stress com {N_POINTS} pontos...")
    print(f"Serão realizadas {N_RUNS} execuções. Apenas a última será considerada.")

    # Variáveis para armazenar os resultados da última execução
    last_scipy_metrics, last_scipy_voronoi = None, None
    last_bw_metrics, last_bw_generator = None, None
    last_points = None

    for i in range(N_RUNS):
        print(f"  > Execução {i+1}/{N_RUNS}...", end="", flush=True)
        
        # Gera novos pontos aleatórios (0-10000 para espalhar bem 10k pontos)
        current_points = np.array([[random.uniform(0, 5000), random.uniform(0, 5000)] for _ in range(N_POINTS)])
        
        # Executa Fortune (SciPy)
        s_metrics, s_voronoi = run_scipy_fortune(current_points)
        
        # Executa Bowyer-Watson (Cython)
        b_metrics, b_generator = run_bowyer_watson_cython(current_points)
        
        # Se for a última execução, salva os dados
        if i == N_RUNS - 1:
            last_scipy_metrics = s_metrics
            last_scipy_voronoi = s_voronoi
            last_bw_metrics = b_metrics
            last_bw_generator = b_generator
            last_points = current_points
            print(" DADOS COLETADOS.")
        else:
            print(" Concluído (dados descartados).")

    print("\nGerando gráficos e relatórios...")

    # --- Plotagem dos Gráficos de Métricas (Bar Chart) ---
    labels = ['Tempo (s)', 'Memória (MB)']
    
    scipy_vals = [last_scipy_metrics['execution_time_sec'], last_scipy_metrics['peak_memory_mb']]
    bw_vals = [last_bw_metrics['execution_time_sec'], last_bw_metrics['peak_memory_mb']]

    x = np.arange(len(labels))
    width = 0.35

    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig1.suptitle(f'Comparação de Performance (N={N_POINTS})', fontsize=16)

    # Gráfico de Tempo
    rects1 = ax1.bar(['Fortune', 'Bowyer-Watson'], [scipy_vals[0], bw_vals[0]], color=['tab:blue', 'tab:orange'])
    ax1.set_ylabel('Segundos')
    ax1.set_title('Tempo de Execução')
    ax1.bar_label(rects1, fmt='%.4f')

    # Gráfico de Memória
    rects2 = ax2.bar(['Fortune', 'Bowyer-Watson'], [scipy_vals[1], bw_vals[1]], color=['tab:blue', 'tab:orange'])
    ax2.set_ylabel('Megabytes (MB)')
    ax2.set_title('Pico de Memória')
    ax2.bar_label(rects2, fmt='%.2f')

    # --- Plotagem Visual dos Diagramas (Visualização Densa) ---
    fig2, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig2.suptitle(f'Visualização dos Diagramas ({N_POINTS} pontos)', fontsize=16)

    # Fortune
    ax_scipy = axes[0]
    voronoi_plot_2d(last_scipy_voronoi, ax=ax_scipy, show_vertices=False, show_points=False, line_colors='blue', line_width=0.5, line_alpha=0.6)
    # Plotamos os pontos manualmente para ter controle do tamanho
    ax_scipy.scatter(last_points[:,0], last_points[:,1], s=1, c='black', marker='.')
    ax_scipy.set_title('Fortune (SciPy)')
    ax_scipy.axis('equal')
    ax_scipy.set_xticks([])
    ax_scipy.set_yticks([])

    # Bowyer-Watson
    ax_bw = axes[1]
    
    # Diagnóstico
    num_edges = len(last_bw_generator.voronoi_edges)
    print(f"\n[DEBUG] Preparando plot do Bowyer-Watson com {num_edges} arestas.")
    
    # Plotar as arestas de Voronoi geradas pelo Bowyer-Watson
    from matplotlib.collections import LineCollection
    
    lines = []
    voronoi_vertices_x = []
    voronoi_vertices_y = []
    
    for p1, p2 in last_bw_generator.voronoi_edges:
        lines.append([(p1.x, p1.y), (p2.x, p2.y)])
        # Coletar vértices para plotagem (pode haver duplicatas, não tem problema para visualização rápida)
        voronoi_vertices_x.append(p1.x)
        voronoi_vertices_y.append(p1.y)
        voronoi_vertices_x.append(p2.x)
        voronoi_vertices_y.append(p2.y)
    
    if lines:
        lc = LineCollection(lines, colors='red', linewidths=0.5, alpha=0.8, label='Arestas Voronoi')
        ax_bw.add_collection(lc)
    else:
        print("[AVISO] Nenhuma aresta encontrada para plotar no Bowyer-Watson!")

    # Plotar vértices de Voronoi (pontos de intersecção das arestas)
    if voronoi_vertices_x:
         ax_bw.scatter(voronoi_vertices_x, voronoi_vertices_y, s=2, c='orange', marker='.', alpha=0.6, label='Vértices Voronoi', zorder=2)

    # Plotar pontos originais (sítios)
    ax_bw.scatter(last_points[:,0], last_points[:,1], s=1, c='black', marker='.', zorder=3, label='Sítios')
    
    ax_bw.set_title('Bowyer-Watson (Cython)')
    ax_bw.axis('equal')
    
    # Definir limites baseados nos pontos reais (com margem de 5%) para garantir visualização correta
    min_x, max_x = np.min(last_points[:, 0]), np.max(last_points[:, 0])
    min_y, max_y = np.min(last_points[:, 1]), np.max(last_points[:, 1])
    
    margin_x = (max_x - min_x) * 0.05
    margin_y = (max_y - min_y) * 0.05
    
    final_xlim = (min_x - margin_x, max_x + margin_x)
    final_ylim = (min_y - margin_y, max_y + margin_y)
    
    # Aplicar limites forçados em ambos os gráficos
    ax_scipy.set_xlim(final_xlim)
    ax_scipy.set_ylim(final_ylim)
    
    ax_bw.set_xlim(final_xlim)
    ax_bw.set_ylim(final_ylim)

    ax_bw.set_xticks([])
    ax_bw.set_yticks([])
    # ax_bw.legend(loc='upper right', fontsize='small') # Legenda pode poluir com tantos dados

    # --- Exibição de Métricas no Console ---
    print("\n--- Resultados Finais (Última Execução) ---")
    print(f"{'Métrica':<25} | {'Fortune (SciPy)':<20} | {'Bowyer-Watson':<20}")
    print("-" * 70)
    print(f"{'Tempo de Execução':<25} | {last_scipy_metrics['execution_time_sec']:.6f} s        | {last_bw_metrics['execution_time_sec']:.6f} s")
    print(f"{'Memória (Pico)':<25} | {last_scipy_metrics['peak_memory_mb']:.4f} MB         | {last_bw_metrics['peak_memory_mb']:.4f} MB")
    print(f"{'Vértices Voronoi':<25} | {last_scipy_metrics['voronoi_vertices']:<20} | {last_bw_metrics['voronoi_vertices']:<20}")
    print(f"{'Arestas Voronoi':<25} | {last_scipy_metrics['voronoi_edges']:<20} | {last_bw_metrics['voronoi_edges_created']:<20}")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
