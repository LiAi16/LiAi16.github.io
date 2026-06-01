from backend.benchmark.experiment_runner import run_all_experiments

if __name__ == "__main__":
    outputs = run_all_experiments(repeats_per_scene=4)
    print("实验完成。")
    print(outputs["summary"])
