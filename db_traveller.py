import shutil
import hashlib
from os.path import isdir, getctime, join, getsize, dirname
from os import mkdir, listdir, walk, system, remove, makedirs
import datetime
from tabulate import tabulate
from time import time

class common:
	def listBackups():
		print("Backups: ")
		folder = 'traveller/'
		
		# List to store folder details
		res = []
		
		# Iterate over each item in the folder
		for item in listdir(folder):
			item_path = join(folder, item)
			
			# Check if the item is a directory
			if isdir(item_path):
				# Get the creation time of the folder
				creation_time = getctime(item_path)
				creation_time_str = datetime.date.fromtimestamp(creation_time).strftime('%Y-%m-%d')
				

				# size
				total_size = 0
				for dirpath, dirnames, filenames in walk(item_path):
					for f in filenames:
						fp = join(dirpath, f)
						total_size += getsize(fp)
				size_mb = total_size / (1024 * 1024)

				# Append folder details to the list
				res.append([item, f"{size_mb:.2f} MB", creation_time_str])
		
		# Print the table
		print(tabulate(res, headers=['Name', 'Size', 'Last Created'], tablefmt='mixed_grid'))
	
	def stopMysql():
		system("cmd /c net stop MySQL8")

	def startMysql():
		system("cmd /c net start MySQL8")

	def get_file_paths(folder):
		file_paths = []
		for root, directories, files in walk(folder):
			for filename in files:
				file_paths.append(join(root, filename))
		return file_paths
	
	def diff_file_hashes(file_path1, file_path2):
		def get_file_hash(file_path):
			hasher = hashlib.sha256()
			with open(file_path, 'rb') as f:
				while chunk := f.read(8192):
					hasher.update(chunk)
			return hasher.hexdigest()
		
		hash1 = get_file_hash(file_path1)
		hash2 = get_file_hash(file_path2)
		
		return hash1 != hash2


class Command:
	def execute(self):
		pass

class viewBackup(Command):
	def execute(self):
		common.listBackups()

class createBackup(Command):
	def execute(self):
		common.listBackups()
		def create(pth):
			if not isdir(pth):
				# Create the parent directory if it doesn't exist
				if not isdir('traveller'):
					mkdir('traveller')
				# Create the destination directory
				mkdir(pth)

		# Source directory
		src = 'data'

		# Destination directory
		dst = f'traveller/{input('Name of the backup> ')}'
		if isdir(dst):
			print("Path exists. Please delete first.")
			return
		
		common.stopMysql()
		create(dst)
		print("Copying...")
		# Copy the entire directory tree
		shutil.copytree(src, dst, dirs_exist_ok=True)
		common.startMysql()
		print("Done!")  

class applyBackup(Command):
	def execute(self):
		common.listBackups()
		base_path = f'traveller\\{input("Input backup name> ").replace('\\', '').replace('/', '')}'
		if not isdir(base_path):
			print("Backup not found.")
			return
		t_start = int(time())
		common.stopMysql()
		ls_back = common.get_file_paths(base_path)
		ls_data = common.get_file_paths('data')
		
		map_back = {}
		map_data = {}

		for L in ls_back:
			map_back[L] = True
		for L in ls_data:
			map_data[L] = True

		f_add = []
		f_rem = []
		f_rep = []

		print("Checking modifications...")
		# mark add / replace
		for F in ls_back:
			dat_p = str(F).replace(base_path, 'data', 1)
			if dat_p not in map_data:
				f_add.append(F)
			elif common.diff_file_hashes(F, dat_p):
				f_rep.append(F)

		# mark remove
		for F in ls_data:
			bak_p = str(F).replace('data\\', base_path + '\\', 1)
			if bak_p not in map_back:
				f_rem.append(F)
				
		for addF in f_add: # use backup
			print("Adding: " + addF)
			tgt = str(addF).replace(base_path, 'data', 1)
			makedirs(dirname(tgt), exist_ok=True)
			shutil.copy2(addF, tgt)

		for repF in f_rep: # use backup
			print("Replacing: " + repF)
			shutil.copy2(repF, str(repF).replace(base_path, 'data', 1))

		for remF in f_rem:
			print("Removing: " + remF)
			remove(remF)

		print("-"*100)
		print(f'No. of operations: Add {len(f_add)} + Remove {len(f_rem)} + Replace {len(f_rep)} = {len(f_add) + len(f_rem) + len(f_rep)}')

		common.startMysql()
		print(f"Done! Time elapsed: {int(time()) - t_start}s")

class deleteBackup(Command):
	def execute(self):
		common.listBackups()
		backupName = f'traveller/{input("Input backup name> ")}'
		if isdir(backupName):
			print("Removing...")
			shutil.rmtree(backupName)
		else:
			print("Backup not found.")
		

class ExitCommand(Command):
	def execute(self):
		print("Exiting program")
		exit()

class Menu:
	def __init__(self):
		self.commands = {
			'1': viewBackup(),
			'5': createBackup(),
			'10': applyBackup(),
			'15': deleteBackup(),
			'99': ExitCommand()
		}

	def show_menu(self):
		print("Menu:")
		print("(1) View backups")
		print("(5) Create full backup")
		print("(10) Apply backup")
		print("(15) Delete backup")
		print("(99) Exit")

	def run_command(self, option):
		command = self.commands.get(option)
		if command:
			command.execute()
		else:
			print("Invalid option")

if __name__ == "__main__":
	menu = Menu()
	if not isdir('traveller'):
		mkdir('traveller')
	while True:
		menu.show_menu()
		option = input("Option number> ")
		menu.run_command(option)
