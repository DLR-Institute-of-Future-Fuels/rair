import test_data_versioning

p1 = 5.5
p2 = 9.5

path = test_data_versioning.get_result_directory_name()

with open(path + "testresult.txt", "w") as f:
    f.write(f"result = {p1 + p2}\n")
