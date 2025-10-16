"""
Script para comparar a performance dos algoritmos de Voronoi:
- Algoritmo de Fortune (implementado com SciPy)
- Algoritmo de Bowyer-Watson (implementação manual)

O script executa ambos os algoritmos em conjuntos de dados de tamanhos variados,
coleta métricas de tempo e memória, e plota gráficos comparativos.
"""

import time
import tracemalloc
import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d

# Importa a classe do nosso arquivo Bowyer-Watson
from Bowyer.bowyer_watson import BowyerWatson


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

def run_bowyer_watson(points):
    """ Executa nossa implementação do Bowyer-Watson e coleta métricas. """
    tracemalloc.start()
    start_time = time.perf_counter()

    bw_generator = BowyerWatson(points)
    bw_generator.run()
    metrics = bw_generator.metrics

    metrics["execution_time_sec"] = time.perf_counter() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics["peak_memory_mb"] = peak_mem / (1024 * 1024)
    
    return metrics, bw_generator

def main():
    """ Função principal que orquestra os testes e a plotagem. """
    # Define os tamanhos dos problemas a serem testados
    site_counts = [10, 25, 50, 100, 250, 500, 1000, 2000]
    
    results_scipy = []
    results_bw = []

    # Armazena os diagramas para plotagem posterior
    diagrams_to_plot = {10: {}, 100: {}, 1000: {}}

    print("Iniciando a comparação de performance...")

    for count in site_counts:
        print(f"Executando para {count} sítios...")

        if count == 10:
            # Executa 5 vezes para aquecimento, mas salva apenas a última
            print("  - Realizando 5 execuções para aquecimento (warm-up)...")
            for i in range(5):
                points = np.array([[random.uniform(0, 1000), random.uniform(0, 1000)] for _ in range(count)])
                scipy_metrics, scipy_voronoi = run_scipy_fortune(points)
                bw_metrics, bw_generator = run_bowyer_watson(points)
                print(f"    - Execução {i+1}/5 concluída.")
        else:
            # Gera os mesmos pontos para ambos os algoritmos para uma comparação justa
            points = np.array([[random.uniform(0, 1000), random.uniform(0, 1000)] for _ in range(count)])
            # Executa e coleta métricas e diagramas
            scipy_metrics, scipy_voronoi = run_scipy_fortune(points)
            bw_metrics, bw_generator = run_bowyer_watson(points)

        results_scipy.append(scipy_metrics)
        results_bw.append(bw_metrics)

        # Salva os diagramas de interesse
        if count in diagrams_to_plot:
            diagrams_to_plot[count]['scipy'] = (scipy_voronoi, points)
            diagrams_to_plot[count]['bw'] = (bw_generator, points)

    print("Execução concluída. Gerando gráficos...")

    # --- Gráficos de Performance ---
    scipy_times = [r["execution_time_sec"] for r in results_scipy]
    scipy_mem = [r["peak_memory_mb"] for r in results_scipy]
    bw_times = [r["execution_time_sec"] for r in results_bw]
    bw_mem = [r["peak_memory_mb"] for r in results_bw]

    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    fig1.suptitle('Análise de Performance', fontsize=16)

    # Gráfico 1: Tempo de Execução
    ax1.plot(site_counts, scipy_times, 'o-', label='Fortune (SciPy)')
    ax1.plot(site_counts, bw_times, 's-', label='Bowyer-Watson (Manual)')
    ax1.set_title('Tempo de Execução vs. Número de Sítios')
    ax1.set_xlabel('Número de Sítios')
    ax1.set_ylabel('Tempo (segundos) - Escala Logarítmica')
    ax1.set_yscale('log')
    ax1.legend()
    ax1.grid(True, which="both", ls="--")

    # Gráfico 2: Pico de Uso de Memória
    ax2.plot(site_counts, scipy_mem, 'o-', label='Fortune (SciPy)')
    ax2.plot(site_counts, bw_mem, 's-', label='Bowyer-Watson (Manual)')
    ax2.set_title('Pico de Uso de Memória vs. Número de Sítios')
    ax2.set_xlabel('Número de Sítios')
    ax2.set_ylabel('Memória (MB)')
    ax2.legend()
    ax2.grid(True)
    
    fig1.tight_layout(rect=[0, 0.03, 1, 0.95], h_pad=3)

    # --- Gráficos de Comparação Visual dos Diagramas (em janelas separadas) ---
    plot_counts = [10, 100, 1000]

    for count in plot_counts:
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle(f'Comparação Visual para {count} Sítios', fontsize=16)

        # Plotagem do SciPy (Fortune)
        ax_scipy = axes[0]
        if count in diagrams_to_plot and 'scipy' in diagrams_to_plot[count]:
            voronoi_data, points_data = diagrams_to_plot[count]['scipy']
            voronoi_plot_2d(voronoi_data, ax=ax_scipy, show_vertices=False, line_colors='orange', line_width=2, point_size=2)
            ax_scipy.set_title(f'Fortune (SciPy) - {count} Sítios')
            ax_scipy.set_aspect('equal', adjustable='box')
            ax_scipy.set_xticks([])
            ax_scipy.set_yticks([])

        # Plotagem do Bowyer-Watson
        ax_bw = axes[1]
        if count in diagrams_to_plot and 'bw' in diagrams_to_plot[count]:
            bw_data, points_data_bw = diagrams_to_plot[count]['bw']
            ax_bw.plot(points_data_bw[:, 0], points_data_bw[:, 1], 'o', color='red', markersize=2)
            for p1, p2 in bw_data.voronoi_edges:
                ax_bw.plot([p1.x, p2.x], [p1.y, p2.y], 'b-')
            ax_bw.set_title(f'Bowyer-Watson - {count} Sítios')
            ax_bw.set_aspect('equal', adjustable='box')
            ax_bw.set_xticks([])
            ax_bw.set_yticks([])
        
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    # --- Tabela Comparativa para o Maior Conjunto de Dados ---
    last_scipy_results = results_scipy[-1]
    last_bw_results = results_bw[-1]
    last_count = site_counts[-1]

    # Adiciona unidades de medida diretamente nas células
    table_content = [
        [f"{last_scipy_results['voronoi_vertices']}", f"{last_bw_results['voronoi_vertices']}"],
        [f"{last_scipy_results['voronoi_edges']}", f"{last_bw_results['voronoi_edges_created']}"],
        [f"{last_scipy_results['peak_memory_mb']:.4f} MB", f"{last_bw_results['peak_memory_mb']:.4f} MB"],
        [f"{last_scipy_results['execution_time_sec']:.4f} s", f"{last_bw_results['execution_time_sec']:.4f} s"]
    ]
    row_labels = ["Vértices Voronoi", "Arestas Voronoi", "Pico de Memória", "Tempo de Execução"]
    col_labels = ["Fortune (SciPy)", "Bowyer-Watson"]

    # Define cores para cabeçalhos e linhas
    row_colors = ['#F0F8FF', '#F0F8FF', '#F0F8FF', '#F0F8FF']
    col_colors = ['#DDEBF7', '#DDEBF7']

    fig_table, ax_table = plt.subplots(figsize=(10, 3))
    ax_table.axis('tight')
    ax_table.axis('off')
    
    # Cria a tabela com cores
    table = ax_table.table(
        cellText=table_content, 
        rowLabels=row_labels, 
        rowColours=row_colors,
        colLabels=col_labels, 
        colColours=col_colors,
        loc='center', 
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)
    
    ax_table.set_title(f'Comparativo de Métricas para {last_count} Sítios', fontweight="bold", pad=20)

    # Usa tight_layout para centralizar a tabela e garantir que tudo seja visível
    fig_table.tight_layout(pad=1.5)

    plt.show()

if __name__ == "__main__":
    main()
