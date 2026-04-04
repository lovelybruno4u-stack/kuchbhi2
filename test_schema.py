with open('app.py', 'r') as f:
    for line in f:
        if "'quiz':" in line:
            print(line.strip())
