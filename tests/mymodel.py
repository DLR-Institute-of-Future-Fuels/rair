import time

print('Test text output to stdio')
p1 = 5.9
p2 = 9.5

with open("test_result.txt", "w") as f:
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"Current time: {current_time}\n")
    f.write(f"result = {p1 + p2}\n")
