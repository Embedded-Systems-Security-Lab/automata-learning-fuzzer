from FMI.projects.project import Project
import os
import pickle

proj_name = "Temp_folder"
proj = Project(proj_name)
file_path = os.path.join(proj_name,"text.txt")
data = [b'h\x0e\x00\x00\x00\x00F\x01\x04\x00\n\x00\x00\x00\x00\x00', b'\xe8\x0e\x00\x00\x00\x00F\x01\x04\x00\n\x00\x00\x00\x00\x00', b'\xe8\x0e\x00\x00\x00\x00F\x01\x04\x00\n\x00\x00\x00\x00\x00',
        b'h\x8e\x0e\x00`\x00/\x01\x06\x00\n\x00\x0c\x00\x00\x01', b'h\x8e\x0e\x00`\x00/\x01\x06\x00\n\x00\x0c\x00\x00\x01']

print(data)
# for d in data:
#     print(bytearray(d))
# print(file_path, os.path.exists(file_path))

proj.write_array(data, file_path)
print(proj.read_data(file_path))
# with open(file_path, 'wb') as f:
#     pickle.dump(data, f)

# with open(file_path, 'rb') as f:
#     new_data = pickle.load(f)

# print(new_data)
