x = [i for i in range(10)]
for e in x:
    if e > 11:
        print('early exit from for')
        break
else:
    print('for else block')