import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

len_trs = []
bws = []
transes = []
times = []

for i in range(1,4):
    file_name = "./stats/node" + str(i) + "_stats.csv"
    raw = pd.read_csv(file_name, usecols=['transaction', 'recv_time', 'process_time','cur_bytes'])
    stats = np.array(raw)

    trans = np.array(stats[:, 0])
    recv_time = np.array(stats[:, 1], dtype='float')
    process_time = np.array(stats[:, 2], dtype='float')
    amount_data = np.array(stats[:, 3], dtype='int')
    # print(process_time[0],recv_time[0])

    transes.append(trans)
    len_trs.append(len(trans))
    bws.append( (amount_data[-1]-amount_data[0])/(process_time[-1]-process_time[0])/1000 )
    times.append(process_time)
    times.append(recv_time)

r = min(len_trs)
for i in range(len(times)):
    times[i] = times[i][:r]
vtimes = np.vstack(times)

fail_time = 144
delays = []
for i in range(r):

    flag = True
    if i < fail_time:
        gt = transes[0][i]
        for j in range(3):
            if transes[j][i]!= gt:
                flag = False
                break
        if flag:
            delays.append(max(vtimes[:,i])-min(vtimes[:,i]))
        else:
            delays.append(999)
    else:
        gt = transes[1][i]
        for j in range(1,3):
            if transes[j][i]!= gt:
                flag = False
                break
        if flag:
            delays.append(max(vtimes[1:,i])-min(vtimes[1:,i]))
        else:
            delays.append(999)
print("bandwidth at each node",bws)

fig1 = plt.figure()
plt.plot(np.arange(r), delays)
plt.xlabel('Transactions')
plt.ylabel('Process delay [sec]')
fig1.savefig('./plots/delays3.png', dpi=fig1.dpi)

