class HelloWorldPrinter:
    """ example class """
    def print_hello_world(self):
        print("Hello, world!")

def greetings():
    """ example function """
    h = HelloWorldPrinter()
    h.print_hello_world()

# call the greetings function
greetings()
