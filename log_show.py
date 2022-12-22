import matplotlib.pyplot as plt
val_loss = []
train_loss = []
with open("./models/transduction_model_kyosuke_2400/log.txt", "r") as f:
    log = f.readlines()
    print(log[5:2405])
    for line in log[5:2405]:
        _log = line.split(" ")
        val_loss.append(float(_log[6]))
        train_loss.append(float(_log[9]))
        # print(line.split(" "))
plt.plot(train_loss)
plt.plot(val_loss)
plt.show()




