import sys
from filehandler import FileHandler
from packagehandler import PackageHandler

class CommandHandler:
    
    VERSION = '0.001'

    def __init__(self, options):
        self.options = options
        
    def run(self):
        if (self.options['command'] == 'listpackages'):
            try:
                projectPath = self.options[0]
            except KeyError:
                projectPath = ""
            self.listPackages(projectPath)
        if (self.options['command'] == 'createproject'):
            self.verifyOption(0)
            self.createProject(self.options[0])
        if (self.options['command'] == 'updatepackage'):
            self.verifyOption(0)
            self.updatePackage(self.options[0])
        if (self.options['command'] == 'buildproject'):
            self.verifyOption(0)
            self.buildProject(self.options[0])
        if (self.options['command'] == 'addpackage'):
            self.verifyOption(1)
            self.addPackage(self.options[1], self.options[0])
        if (self.options['command'] == 'removepackage'):
            self.verifyOption(1)
            self.removePackage(self.options[1], self.options[0])
        if (self.options['command'] == 'zippackage'):
            self.verifyOption(0)
            FileHandler.zipPackage(self.options[0])
            
    def verifyOption(self, optionName):
        if (self.options.get(optionName, '') == ''):
            print("Required option '" + str(optionName) + "' missing")
            sys.exit(1)

    def createProject(self, projectPath):
        if(not FileHandler.createFolder(projectPath)):
            print("Project or folder '" + projectPath + "' already exists")
            sys.exit(1)
        FileHandler.createFolder(projectPath + '/pk3/maps')
        ph = PackageHandler(projectPath)
        ph.saveProjectDescription({})
        print ("Created project '" + projectPath + "'")

    def updatePackage(self, packageName):
        PackageHandler.updatePackage(packageName)
    
    def buildProject(self, projectPath):
        if(not FileHandler.fileExists(projectPath)):
            print("Project '" + projectPath + "' doesn't exist")
            sys.exit(1)
        ph = PackageHandler(projectPath)
        ph.buildProject()
        
    def addPackage(self, packageName, projectPath):
        if(not FileHandler.fileExists(projectPath)):
            print("Project '" + projectPath + "' doesn't exist")
            sys.exit(1)
        ph = PackageHandler(projectPath)
        ph.installPackageTree(packageName)

    def removePackage(self, packageName, projectPath):
        if(not FileHandler.fileExists(projectPath)):
            print("Project '" + projectPath + "' doesn't exist")
            sys.exit(1)
        ph = PackageHandler(projectPath)
        ph.removePackageFromProject(packageName)
        
    def listPackages(self, projectPath):
        ph = PackageHandler(projectPath)
        ph.listPackages()