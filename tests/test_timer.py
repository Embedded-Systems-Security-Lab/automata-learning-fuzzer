from FMI.utils.time import Timer


with Timer() as t:
    print("hello")
print(t.elapsed_time())
