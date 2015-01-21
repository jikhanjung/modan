# -*- mode: python -*-

block_cipher = None

icontree = Tree('./icon', prefix='icon')
configtree = Tree('./config', prefix='config')
freeglut = [('freeglut.dll','C:\\Users\\jikhanjung\\git\\modan\\freeglut.dll','BINARY')]

a = Analysis(['modan.py'],
             pathex=['C:\\Users\\jikhanjung\\git\\modan'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             cipher=block_cipher)
pyz = PYZ(a.pure,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='modan.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='\\Users\\jikhanjung\\git\\modan\\icon\\modan.ico')
coll = COLLECT(exe,
               a.binaries,
               icontree,
               configtree,
               freeglut,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='modan')
