import cvxpy as cp
import mosek
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.pyplot import MultipleLocator
K = 4
hmin = 100
qn = np.array([[751, 751, hmin], [100, 898, hmin], [400, 0, hmin], [100, 592, hmin]])
s = np.array([[750, 750, 0], [100, 900, 0], [400, 0, 0], [100, 600, 0]])
q0 = np.array([[0, 30, 100], [30, 30, 100], [0, 0, 100], [30, 0, 100]])
qn = np.array([[751, 751, hmin], [100, 898, hmin], [400, 0, hmin], [100, 592, hmin]])
#find Vme with SCA
def cvx_find_Vmr(vc):
    sc = math.sqrt(vc**2 + math.sqrt(vc**4 + 32855))
    v = cp.Variable()
    s = cp.Variable(nonneg=True)
    objfunc = []
    objfunc.append(cp.inv_pos(s) * 5194.8 + 0.002 * v**3)
    constr = []
    constr.append(v >= 1)
    constr.append(v <= 40)
    constr.append(s**2 * (sc**3) <= 32855 * sc - 65710 * (s - sc) + 4 * v * vc *(sc**3) - 2 * vc**2 * (sc**3))
    prob = cp.Problem(cp.Minimize(sum(objfunc)), constr)
    prob.solve(solver=cp.MOSEK)
    print(v.value)
    return v.value
#trajectory_initialization
def path_init():
    q = []
    time = [28.37, 23.73, 10.9, 16.24]
    q.append(np.array([
        [0, 30, 100],
        [30, 30, 130],
        [0, 0, 190],
        [30, 0, 160]
    ]))
    Vme = [((qn[k][0] - q[0][k][0]) / time[k], (qn[k][1] - q[0][k][1]) / time[k]) for k in range(K)]
    h = [100, 130, 190, 160]
    print(Vme)
    for i in range(1, 11):
        q.append(np.array([[q[0][k][0] + i * Vme[k][0], q[0][k][1] + i * Vme[k][1], h[k]] for k in range(K)]))
        # print(q[i])
    # q[11]
    q.append(np.array([[291.18787452, 309.55586888, 100], [62.44837758, 432.35988201, 130], [400, 0, 160],
                       [77.4137931, 400.98522167, 160]]))
    Vme1 = [[26.471624955939372, 25.41416989777934], [2.949852507374631, 36.57817109144543], [0, 0],
            [4.310344827586207, 36.45320197044335]]
    # q[12]----q[16]
    h1 = [100, 130, 100, 160]
    for i in range(1, 6):
        q.append(np.array([[q[11][k][0] + i * Vme1[k][0], q[11][k][1] + i * Vme1[k][1], h1[k]] for k in range(K)]))
    # q[17]
    q.append(
        np.array([[450.01762426, 462.04088827, 100], [80.14749262, 651.82890856, 130], [400, 0, 100], [100, 592, 130]]))
    Vme2 = [[26.471624955939372, 25.41416989777934], [2.949852507374631, 36.57817109144543], [0, 0], [0, 0]]
    # q[18]----q[23]
    h2 = [100, 130, 100, 100]
    for i in range(1, 7):
        q.append(np.array([[q[17][k][0] + i * Vme2[k][0], q[17][k][1] + i * Vme2[k][1], h2[k]] for k in range(K)]))
    # q[24]
    q.append(np.array([[635.31899895, 639.94007755, 100], [100, 898, 100], [400, 0, 100], [100, 592, 100]]))
    Vme3 = [[26.471624955939372, 25.41416989777934], [0, 0], [0, 0], [0, 0]]
    # q[25]----q[28]
    for i in range(1, 5):
        q.append(np.array([[q[24][k][0] + i * Vme3[k][0], q[24][k][1] + i * Vme3[k][1], hmin] for k in range(K)]))
    # q[29]----q[39]
    for i in range(1, 12):
        q.append(np.array([[751, 751, 100], [100, 898, 100], [400, 0, 100], [100, 592, 100]]))
    print(q)
#find_hovering_locations
def find_hoovering_point(qc):
    ir = [0 for _ in range(K)]
    ir1 = [0 for _ in range(K)]

    # update ir
    for k in range(K):
        ik = 0
        for j in range(K):
            ik += 1 / ((np.linalg.norm(qc[j] - s[k])) ** 2)
        ir1[k] = ik

    for k in range(K):
        ik = 0
        for j in range(K):
            if j != k:
                # 来自其它base station的干扰 -------(18)------算法1，步骤5
                ik += 1 / ((np.linalg.norm(qc[j] - s[k])) ** 2)
        ir[k] = ik

    q = []
    for k in range(K):
        q.append(cp.Variable(shape=(3)))

    objfunc = []
    for k in range(K):
        term1 = 0
        for j in range(K):
            term1 += -1 * (cp.norm(q[j] - s[k]) ** 2 - (cp.norm(qc[j] - s[k]) ** 2)) / (
                    np.linalg.norm(qc[j] - s[k]) ** 4)
            objfunc.append(term1 / (1 + ir1[k]))
        objfunc.append(math.log(ir1[k] + 1))

        term2 = []
        for j in range(K):
            ratio = -1 / (1 + ir[k])
            if j != k:
                det = np.linalg.norm(qc[j] - s[k]) ** 2 + 2 * (qc[j] - s[k]).transpose() * (q[j] - qc[j])
                term2.append(ratio * cp.inv_pos(det))
        # sum
        objfunc.append(cp.sum(term2))

    constr = []
    for k in range(K):
        constr.append(q[k][2] == 100)
        for j in range(2):
            constr.append(q[k][j] >= 0)
            constr.append(q[k][j] <= 1000)

    # sum
    prob = cp.Problem(cp.Maximize(sum(objfunc)), constr)
    prob.solve()
    print("optimal value", prob.value)
    return [qv.value for qv in q], prob.value
#GREEN
def finished_green(qc, lll, kkk):
    yc = [[0 for _ in range(K)] for _ in range(40)]
    ir1 = [[0 for _ in range(K)] for _ in range(40)]
    ir2 = [[0 for _ in range(K)] for _ in range(40)]
    for m in range(40):
        for k in range(K):
            ik = 0
            for j in range(K):
                ik += 1 / ((np.linalg.norm(qc[m][j] - s[k])) ** 2)
            ir1[m][k] = ik
    for m in range(40):
        for k in range(K):
            ik = 0
            for j in range(K):
                if j != k:
                    # co-interfernece
                    ik += 1 / ((np.linalg.norm(qc[m][j] - s[k])) ** 2)
            ir2[m][k] = ik
    for m in range(1, 40):
        for k in range(K):
            yc[m][k] = math.sqrt(np.linalg.norm(qc[m][k][0:2] - qc[m - 1][k][0:2]) ** 2 + math.sqrt(
                np.linalg.norm(qc[m][k][0:2] - qc[m - 1][k][0:2]) ** 4 + 32855))
    q = []
    y = []
    for n in range(40):
        q.append(cp.Variable(shape=(K, 3)))
        y.append(cp.Variable(shape=(K, 1), nonneg=True))
    objfunc = []
    for m in range(40):
        for k in range(K):
            term1 = 0
            for j in range(K):
                term1 += -1.44 * (cp.norm(q[m][j] - s[k]) ** 2 - (cp.norm(qc[m][j] - s[k]) ** 2)) / (
                        np.linalg.norm(qc[m][j] - s[k]) ** 4)
                objfunc.append(kkk * term1 / (1 + ir1[m][k]))
            objfunc.append(kkk * math.log(ir1[m][k] + 1) / math.log(2))

            term2 = []
            for j in range(K):
                ratio = -1 / (1 + ir2[m][k])
                if j != k:
                    det = np.linalg.norm(qc[m][j] - s[k]) ** 2 + 2 * (qc[m][j] - s[k]).transpose() * (
                            q[m][j] - qc[m][j])
                    term2.append(ratio * cp.inv_pos(det))
            # sum
            objfunc.append(kkk * (cp.sum(term2) - math.log(1 + ir2[m][k]) + (ir2[m][k] / (1 + ir2[m][k]))))

    # ------------------------------------------------ENERGY CONSUMPTION
    for n in range(1, 40):
        for k in range(K):
            # lamuda = 0.01, work on Dinkelbach's algorithm
            objfunc.append(-1 * lll * (cp.inv_pos(y[n][k]) * 5194.8 + 0.002 * cp.norm(q[n][k][0:2] - q[n - 1][k][0:2]) ** 3))


    constr = []
    for n in range(1, 40):
        for k in range(K):
            constr.append((y[n][k] ** 2) * (yc[n][k] ** 3) <= 32855 * yc[n][k] - 65710 * (y[n][k] - yc[n][k]) + 4 * (
                    qc[n][k][0:2] - qc[n - 1][k][0:2]).transpose() * (q[n][k][0:2] - q[n - 1][k][0:2])
                          * (yc[n][k] ** 3) - 2 * (cp.norm(qc[n][k][0:2] - qc[n - 1][k][0:2]) ** 2) * (yc[n][k] ** 3))
            #Vmax = 60
            constr.append(cp.norm(q[n][k][0:2] - q[n - 1][k][0:2]) <= 60)


    for k in range(K):
        constr.append(q[0][k] == q0[k])
        constr.append(q[39][k] == qn[k])

    for n in range(40):
        for k in range(K):
            # constr.append(q[n][k][2] == qc[n][k][2])
            constr.append(q[n][k][2] == 100)
            # dmin=30m
            for j in range(k + 1, K):
                constr.append(
                    2 * (qc[n][k][0:2] - qc[n][j][0:2]).transpose() * (q[n][k][0:2] - q[n][j][0:2]) >= cp.norm(
                        qc[n][k][0:2] - qc[n][j][0:2]) ** 2 + 30 ** 2)

    prob = cp.Problem(cp.Maximize(sum(objfunc)), constr)
    prob.solve(solver=cp.MOSEK)
    print("optimal value", prob.value)
    return [qv.value for qv in q], prob.value
#show_trajectory
def show():
    q_green = np.array([[[0, 30., 100.], [30., 30., 100.], [0, 0, 100.], [30., 0, 100.]],
                        [[32.41217554, 71.39833529, 100], [41.14762573, 74.29223261, 130],
                         [50.06656256, 32.90611026, 100],
                         [32.09603876, 37.73234208, 130]],
                        [[63.88790373, 109.14432287, 100], [56.49047845, 115.38960458, 130],
                         [98.23208662, 42.0366214, 100],
                         [34.45730705, 75.54380709, 100]],
                        [[96.37908774, 144.52820072, 100],
                         [65.2385903, 156.38357954, 100],
                         [144.3637183, 30.70607654, 100],
                         [40.42818913, 114.18926708, 100]], [[128.47816639, 176.6752084, 100],
                                                             [75.39065082, 196.14002375, 100],
                                                             [190.57337332, 20.70715, 100],
                                                             [41.05424462, 151.86402832, 100]],
                        [[159.74723369, 205.44091294, 100],
                         [89.58426374, 233.79236545, 100],
                         [235.45642595, 12.83601576, 100],
                         [43.54273261, 187.62460609, 100]], [[190.4682637, 231.5355901, 100],
                                                             [100.68227993, 270.81022098, 100],
                                                             [278.05668011, 7.27954211, 100],
                                                             [46.26240256, 223.22224677, 100]],
                        [[220.51304756, 255.95640573, 100],
                         [107.13902031, 307.85853267, 100],
                         [318.27261111, 3.77788617, 100],
                         [47.36209916, 259.71387403, 100]], [[249.9307085, 279.542317, 100],
                                                             [110.60099599, 344.94282262, 100],
                                                             [354.69784876, 1.82224069, 100],
                                                             [48.2013551, 296.86064109, 100]],
                        [[284.92802405, 304.27667346, 100],
                         [113.12591254, 382.06589634, 100],
                         [378.01812801, 0.85534062, 100],
                         [50.12782335, 334.00883718, 100]], [[307.68256521, 328.79424362, 100],
                                                             [115.32966838, 419.35571196, 100],
                                                             [396.18515087, 0.45884458, 100],
                                                             [52.86625143, 370.66709126, 100]],
                        [[3.31416134e+02, 3.55052374e+02, 100],
                         [1.16010103e+02, 4.56916218e+02, 100],
                         [4.12373180e+02, 3.59370568e-01, 100],
                         [5.57201182e+01, 4.06715800e+02, 100]], [[3.54516979e+02, 3.80889916e+02, 100],
                                                                  [1.14444637e+02, 4.94601205e+02, 100],
                                                                  [3.99929998e+02, 3.55741562e-01, 100],
                                                                  [5.89275742e+01, 4.42051794e+02, 100]],
                        [[3.76132337e+02, 4.06937785e+02, 100],
                         [1.03195099e+02, 5.33637837e+02, 100],
                         [3.99930244e+02, 3.55198444e-01, 100],
                         [6.29523621e+01, 4.77161518e+02, 100]], [[3.99106152e+02, 4.31991024e+02, 100],
                                                                  [9.60242382e+01, 5.70513922e+02, 100],
                                                                  [3.99930846e+02, 3.54903153e-01, 100],
                                                                  [8.00862823e+01, 5.12344881e+02, 100]],
                        [[4.22182233e+02, 4.56482377e+02, 100],
                         [9.37670822e+01, 6.02942951e+02, 100],
                         [3.99931107e+02, 3.54658449e-01, 100],
                         [9.34651994e+01, 5.47797589e+02, 100]], [[4.44931063e+02, 4.81178342e+02, 100],
                                                                  [9.51646091e+01, 6.31819026e+02, 100],
                                                                  [3.99931194e+02, 3.54511442e-01, 100],
                                                                  [1.00064213e+02, 5.83550273e+02, 100]],
                        [[4.67749338e+02, 5.05853438e+02, 100],
                         [9.58052873e+01, 6.72919638e+02, 100],
                         [3.99931177e+02, 3.54516405e-01, 100],
                         [1.00143932e+02, 6.15762761e+02, 100]], [[4.90580224e+02, 5.31397814e+02, 100],
                                                                  [9.66816919e+01, 7.14735574e+02, 100],
                                                                  [3.99931138e+02, 3.54532332e-01, 100],
                                                                  [1.00139658e+02, 5.95729902e+02, 100]],
                        [[5.12052714e+02, 5.61817238e+02, 100],
                         [9.76908727e+01, 7.56547074e+02, 100],
                         [3.99931116e+02, 3.54517379e-01, 100],
                         [1.00135470e+02, 5.80897039e+02, 100]], [[5.34470964e+02, 5.90717693e+02, 100],
                                                                  [9.82571801e+01, 7.98363631e+02, 100],
                                                                  [3.99931122e+02, 3.54514664e-01, 100],
                                                                  [1.00132286e+02, 5.70278130e+02, 100]],
                        [[5.57026083e+02, 6.19192049e+02, 100],
                         [9.88494319e+01, 8.37908498e+02, 100],
                         [3.99931130e+02, 3.54510318e-01, 100],
                         [1.00129575e+02, 5.61886420e+02, 100]], [[5.80533465e+02, 6.45910336e+02, 100],
                                                                  [9.98855297e+01, 8.75395244e+02, 100],
                                                                  [3.99931128e+02, 3.54523886e-01, 100],
                                                                  [1.00127568e+02, 5.57317003e+02, 100]],
                        [[6.30641943e+02, 6.78905403e+02, 100],
                         [1.00246108e+02, 9.11579852e+02, 100],
                         [3.99931129e+02, 3.54529507e-01, 100],
                         [1.00126177e+02, 5.54414904e+02, 100]], [[6.81563430e+02, 7.10545094e+02, 100],
                                                                  [1.00272226e+02, 9.46132609e+02, 100],
                                                                  [3.99931132e+02, 3.54519682e-01, 100],
                                                                  [1.00125189e+02, 5.52149097e+02, 100]],
                        [[7.13266115e+02, 7.21961152e+02, 100],
                         [1.00269912e+02, 9.28520383e+02, 100],
                         [3.99931134e+02, 3.54532920e-01, 100],
                         [1.00124503e+02, 5.50405520e+02, 100]], [[7.29023846e+02, 7.31716691e+02, 100],
                                                                  [1.00268239e+02, 9.14202361e+02, 100],
                                                                  [3.99931139e+02, 3.54582667e-01, 100],
                                                                  [1.00123835e+02, 5.48811716e+02, 100]],
                        [[7.42609473e+02, 7.43709060e+02, 100],
                         [1.00267294e+02, 9.06434976e+02, 100],
                         [3.99931132e+02, 3.54600525e-01, 100],
                         [1.00123439e+02, 5.47812092e+02, 100]], [[7.55838082e+02, 7.56070376e+02, 100],
                                                                  [1.00266309e+02, 8.98498993e+02, 100],
                                                                  [3.99931129e+02, 3.54688376e-01, 100],
                                                                  [1.00123565e+02, 5.47964076e+02, 100]],
                        [[7.57804048e+02, 7.57920086e+02, 100],
                         [1.00265648e+02, 8.93188990e+02, 100],
                         [3.99931141e+02, 3.54790932e-01, 100],
                         [1.00123984e+02, 5.48695872e+02, 100]], [[7.49426251e+02, 7.49872722e+02, 100],
                                                                  [1.00265463e+02, 8.91653095e+02, 100],
                                                                  [3.99931133e+02, 3.54992927e-01, 100],
                                                                  [1.00124606e+02, 5.49852177e+02, 100]],
                        [[7.49426873e+02, 7.49873250e+02, 100],
                         [1.00265699e+02, 8.93122600e+02, 100],
                         [3.99931156e+02, 3.55264777e-01, 100],
                         [1.00125491e+02, 5.51774588e+02, 100]], [[7.49427218e+02, 7.49873393e+02, 100],
                                                                  [1.00266264e+02, 8.96934845e+02, 100],
                                                                  [3.99931185e+02, 3.55502351e-01, 100],
                                                                  [1.00126406e+02, 5.53744080e+02, 100]],
                        [[7.49427166e+02, 7.49873515e+02, 100],
                         [1.00266806e+02, 9.00450778e+02, 100],
                         [3.99931199e+02, 3.55624081e-01, 100],
                         [1.00127512e+02, 5.55919207e+02, 100]], [[7.49426764e+02, 7.49873482e+02, 100],
                                                                  [1.00266844e+02, 9.00235524e+02, 100],
                                                                  [3.99931200e+02, 3.55741925e-01, 100],
                                                                  [1.00129047e+02, 5.58337349e+02, 100]],
                        [[7.49426808e+02, 7.49873468e+02, 100],
                         [1.00266644e+02, 8.98291107e+02, 100],
                         [3.99931190e+02, 3.55840883e-01, 100],
                         [1.00131304e+02, 5.63097481e+02, 100]], [[7.49426815e+02, 7.49873380e+02, 100],
                                                                  [1.00267591e+02, 9.04559263e+02, 100],
                                                                  [3.99931200e+02, 3.55953589e-01, 100],
                                                                  [1.00133943e+02, 5.71946532e+02, 100]],
                        [[7.49426446e+02, 7.49873189e+02, 100],
                         [1.00269117e+02, 9.15354989e+02, 100],
                         [3.99931183e+02, 3.56160898e-01, 100],
                         [1.00137010e+02, 5.80345149e+02, 100]], [[7.49426189e+02, 7.49873107e+02, 100],
                                                                  [1.00269975e+02, 9.20006741e+02, 100],
                                                                  [3.99931146e+02, 3.56541207e-01, 100],
                                                                  [1.00140666e+02, 5.92142160e+02, 100]],
                        [[751., 751., 100.],
                         [100., 898., 100.],
                         [400., 0, 100.],
                         [100., 592.,
                          100.]]])
    plt.scatter(750, 750, s=320, c='w', edgecolors='#000000', marker='*')
    plt.scatter(100, 900, s=320, c='w', edgecolors='#000000', marker='*')
    plt.scatter(400, 0, s=320, c='w', edgecolors='#000000', marker='*')
    plt.scatter(100, 600, s=320, c='w', edgecolors='#000000', marker='*')
    plt.plot(q_green[0:40, 0, 0], q_green[0:40, 0, 1], '-o', label='UAV 1', linewidth=3, alpha=0.5, c='#87CEFA',
             marker='o', markeredgecolor='b')
    plt.plot(q_green[0:40, 1, 0], q_green[0:40, 1, 1], '-o', label='UAV 2', linewidth=3, alpha=0.5, c='#F08080',
             marker='>', markeredgecolor='r')
    plt.plot(q_green[0:40, 2, 0], q_green[0:40, 2, 1], '-o', label='UAV 3', linewidth=3, alpha=0.5, c='#FFE4B5',
             marker='s', markeredgecolor='#FF8C00')
    plt.plot(q_green[0:40, 3, 0], q_green[0:40, 3, 1], '-o', label='UAV 4', linewidth=3, alpha=0.5, c='#20B2AA',
             marker='D', markeredgecolor='#008000')
    plt.axis([-100, 1000, -100, 1000])
    ax = plt.gca()
    ax.xaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.set_xlabel('x (m)')
    ax.set_ylabel('y (m)')
    plt.grid()
    plt.legend()
    plt.show()
def main():
    #---------------find_Vmr
    # vc = [10]
    # while True:
    #     vc.append(cvx_find_Vmr(vc[-1]))
    #     if math.fabs(vc[-1] - vc[-2]) / vc [-1] <= 0.00001:
    #         break
    #--------------trajectory_initialization
    #path_init()
    #-------------=find_hovering_locations
    # q = [[[750, 750, 100], [100, 900, 100], [400, 0, 100], [100, 600, 100]]]
    # v = [0]
    # while True:
    #     qc, vc = find_hoovering_point(q[-1])
    #     q.append(qc)
    #     v.append(vc)
    #     print(q)
    #     print(v)
    #     if math.fabs(v[-1] - v[-2]) / v [-1] <= 0.0001:
    #         break
    #----------------------------GREEN
    # q = np.array([[[0, 30, 100], [30, 30, 100], [0, 0, 100], [30, 0, 100]],
    #               [[26.47162496, 55.4141699, 100],
    #                [32.94985251, 66.57817109, 130],
    #                [36.69724771, 0, 100],
    #                [34.31034483, 36.45320197, 130]], [[52.94324991, 80.8283398, 100],
    #                                                   [35.89970501, 103.15634218, 130],
    #                                                   [73.39449541, 0, 100],
    #                                                   [38.62068966, 72.90640394, 130]],
    #               [[79.41487487, 106.24250969, 100],
    #                [38.84955752, 139.73451327, 100],
    #                [110.09174312, 0, 100],
    #                [42.93103448, 109.35960591, 100]], [[105.88649982, 131.65667959, 100],
    #                                                    [41.79941003, 176.31268437, 100],
    #                                                    [146.78899083, 0, 100],
    #                                                    [47.24137931, 145.81280788, 100]],
    #               [[132.35812478, 157.07084949, 100],
    #                [44.74926254, 212.89085546, 100],
    #                [183.48623853, 0, 100],
    #                [51.55172414, 182.26600985, 100]], [[158.82974974, 182.48501939, 100],
    #                                                    [47.69911504, 249.46902655, 100],
    #                                                    [220.18348624, 0, 100],
    #                                                    [55.86206897, 218.71921182, 100]],
    #               [[185.30137469, 207.89918928, 100],
    #                [50.64896755, 286.04719764, 100],
    #                [256.88073394, 0, 100],
    #                [60.17241379, 255.17241379, 100]], [[211.77299965, 233.31335918, 100],
    #                                                    [53.59882006, 322.62536873, 100],
    #                                                    [293.57798165, 0, 100],
    #                                                    [64.48275862, 291.62561576, 100]],
    #               [[238.2446246, 258.72752908, 100],
    #                [56.54867257, 359.20353982, 100],
    #                [330.27522936, 0, 100],
    #                [68.79310345, 328.07881773, 100]], [[264.71624956, 284.14169898, 100],
    #                                                    [59.49852507, 395.78171091, 100],
    #                                                    [366.97247706, 0, 100],
    #                                                    [73.10344828, 364.5320197, 100]],
    #               [[291.18787452, 309.55586888, 100],
    #                [62.44837758, 432.35988201, 100],
    #                [400, 0, 100],
    #                [77.4137931, 400.98522167, 100]], [[317.65949948, 334.97003878, 100],
    #                                                   [65.39823009, 468.9380531, 100],
    #                                                   [400, 0, 100],
    #                                                   [81.72413793, 437.43842364, 100]],
    #               [[344.13112443, 360.38420868, 100],
    #                [68.34808259, 505.51622419, 100],
    #                [400, 0, 100],
    #                [86.03448276, 473.89162561, 100]], [[370.60274939, 385.79837857, 100],
    #                                                    [71.2979351, 542.09439528, 100],
    #                                                    [400, 0, 100],
    #                                                    [90.34482758, 510.34482758, 100]],
    #               [[397.07437434, 411.21254847, 100],
    #                [74.24778761, 578.67256638, 100],
    #                [400, 0, 100],
    #                [94.65517241, 546.79802955, 100]], [[423.5459993, 436.62671837, 100],
    #                                                    [77.19764012, 615.25073747, 100],
    #                                                    [400, 0, 100],
    #                                                    [98.96551724, 583.25123152, 100]],
    #               [[450.01762426, 462.04088827, 100],
    #                [80.14749262, 651.82890856, 100],
    #                [400, 0, 100],
    #                [100, 592., 100]], [[476.48924922, 487.45505817, 100],
    #                                    [83.09734513, 688.40707965, 100],
    #                                    [400, 0, 100],
    #                                    [100, 592., 100]], [[502.96087417, 512.86922807, 100],
    #                                                        [86.04719763, 724.98525074, 100],
    #                                                        [400, 0, 100],
    #                                                        [100, 592., 100]],
    #               [[529.43249913, 538.28339796, 100],
    #                [88.99705014, 761.56342183, 100],
    #                [400, 0, 100],
    #                [100, 592., 100]], [[555.90412408, 563.69756786, 100],
    #                                    [91.94690265, 798.14159293, 100],
    #                                    [400, 0, 100],
    #                                    [100, 592., 100]], [[582.37574904, 589.11173776, 100],
    #                                                        [94.89675516, 834.71976402, 100],
    #                                                        [400, 0, 100],
    #                                                        [100, 592., 100]],
    #               [[608.847374, 614.52590766, 100],
    #                [97.84660766, 871.29793511, 100],
    #                [400, 0, 100],
    #                [100, 592., 100]], [[635.31899895, 639.94007755, 100],
    #                                    [100, 898., 100],
    #                                    [400, 0, 100],
    #                                    [100, 592., 100]], [[661.79062391, 665.35424745, 100],
    #                                                        [100, 898., 100],
    #                                                        [400, 0, 100],
    #                                                        [100, 592., 100]],
    #               [[688.26224886, 690.76841735, 100],
    #                [100, 898., 100],
    #                [400, 0, 100],
    #                [100, 592., 100]], [[714.73387382, 716.18258724, 100],
    #                                    [100, 898., 100],
    #                                    [400, 0, 100],
    #                                    [100, 592., 100]], [[741.20549877, 741.59675714, 100],
    #                                                        [100, 898., 100],
    #                                                        [400, 0, 100],
    #                                                        [100, 592., 100]], [[751, 751, 100],
    #                                                                            [100, 898, 100],
    #                                                                            [400, 0, 100],
    #                                                                            [100, 592, 100]],
    #               [[751, 751, 100],
    #                [100, 898, 100],
    #                [400, 0, 100],
    #                [100, 592, 100]], [[751, 751, 100],
    #                                   [100, 898, 100],
    #                                   [400, 0, 100],
    #                                   [100, 592, 100]], [[751, 751, 100],
    #                                                      [100, 898, 100],
    #                                                      [400, 0, 100],
    #                                                      [100, 592, 100]], [[751, 751, 100],
    #                                                                         [100, 898, 100],
    #                                                                         [400, 0, 100],
    #                                                                         [100, 592, 100]],
    #               [[751, 751, 100],
    #                [100, 898, 100],
    #                [400, 0, 100],
    #                [100, 592, 100]], [[751, 751, 100],
    #                                   [100, 898, 100],
    #                                   [400, 0, 100],
    #                                   [100, 592, 100]], [[751, 751, 100],
    #                                                      [100, 898, 100],
    #                                                      [400, 0, 100],
    #                                                      [100, 592, 100]], [[751, 751, 100],
    #                                                                         [100, 898, 100],
    #                                                                         [400, 0, 100],
    #                                                                         [100, 592, 100]],
    #               [[751, 751, 100],
    #                [100, 898, 100],
    #                [400, 0, 100],
    #                [100, 592, 100]], [[751, 751, 100],
    #                                   [100, 898, 100],
    #                                   [400, 0, 100],
    #                                   [100, 592, 100]]])
    # v = [0]
    # #kkk,lll are adjusted according to Dinkelbach's algorithm
    # kkk = 1000
    # lll = 0.001
    # while True:
    #     q, vc = finished_green(q, lll, kkk)
    #     print(q)
    #     v.append(vc)
    #     print(v)
    #     if math.fabs(v[-1] - v[-2]) / v [-1] <= 0.00001:
    #         break
    #--------------------------------------show
    show()


if __name__ == '__main__':
    main()