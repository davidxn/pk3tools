import sys
from filehandler import FileHandler
from packagehandler import PackageHandler

class CommandHandler:
    
    VERSION = '0.001'

    def __init__(self, options):
        self.options = options
        print(self.options)
        
    def run(self):
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

    def createProject(self, projectName):
        if(not FileHandler.createFolder(projectName)):
            print("Project or folder '" + projectName + "' already exists")
            sys.exit(1)
        FileHandler.createFolder(projectName + '/pk3/maps')
        PackageHandler.saveProjectDescription(projectName, {})
        print ("Created project '" + projectName + "'")

    def updatePackage(self, packageName):
        PackageHandler.updatePackage(packageName)
    
    def buildProject(self, projectName):
        if(not FileHandler.fileExists(projectName)):
            print("Project '" + projectName + "' doesn't exist")
            sys.exit(1)
        PackageHandler.buildProject(projectName)
        
    def addPackage(self, packageName, projectName):
        if(not FileHandler.fileExists(projectName)):
            print("Project '" + projectName + "' doesn't exist")
            sys.exit(1)
        PackageHandler.addPackageToProject(packageName, projectName)

    def removePackage(self, packageName, projectName):
        if(not FileHandler.fileExists(projectName)):
            print("Project '" + projectName + "' doesn't exist")
            sys.exit(1)
        PackageHandler.removePackageFromProject(packageName, projectName)