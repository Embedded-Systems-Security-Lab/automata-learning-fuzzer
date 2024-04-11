from FMI import shm


mem = shm.get()

mem.acquire()

print(mem.name)
print(mem.size / 1024)
print(mem.buf)

mem.release()
