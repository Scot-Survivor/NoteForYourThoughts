import pip

__all__ = ["Kivy==2.0.0",
           "pycryptodome~=3.9.9"]
windows = ["kivy-deps.sdl2~=0.3.1",
           "kivy-deps.glew~=0.3.0"]

def install(packages):
	for package in packages:
		pip.main(['install', package])

if __name__ == "__main__":
	from sys import platform
	install(__all__)
	if platform == "windows":
		install(windows)