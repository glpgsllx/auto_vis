import matplotlib.pyplot as plt
import pandas as pd

data = {
    'model_name': ['Claude 3.5 Haiku'] * 8,
    'concurrency': [1, 1, 2, 2, 4, 4, 8, 8],
    'context_length': [128, 256, 128, 256, 128, 256, 128, 256],
    'first_token_latency_ms': [42.5, 45.2, 62.7, 68.3, 95.6, 103.2, 172.4, 188.1],
    'generation_speed_tokens_per_sec': [78.3, 75.6, 145.1, 138.9, 276.4, 265.7, 512.6, 496.3]
}

df = pd.DataFrame(data)

fig, ax1 = plt.subplots(figsize=(12, 8))

color = 'tab:blue'
ax1.set_xlabel('Concurrency')
ax1.set_ylabel('First Token Latency (ms)', color=color)
ax1.plot(df['concurrency'], df['first_token_latency_ms'], color=color, label='First Token Latency (ms)')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Generation Speed (tokens/sec)', color=color)
ax2.plot(df['concurrency'], df['generation_speed_tokens_per_sec'], color=color, linestyle='--', label='Generation Speed (tokens/sec)')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
plt.title('Concurrency Impact on First Token Latency and Generation Speed for Claude 3.5 Haiku')
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.savefig('answer.png')