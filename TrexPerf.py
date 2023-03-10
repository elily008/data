#!/usr/bin/python

import numpy as np

from TrexDriver import *
from Experiment import *

from abc import ABC

class TrexPerfOutput(ExperimentOutput):

    def __init__(self, runs, reqRate, mean, std, olmean, ilmean, opmean, ipmean):
        self.output = {}

        self.output['dl_mean'] = mean
        self.output['dl_std'] = std
        self.output['requested_tx_rate'] = reqRate
        self.output['ol_mean'] = olmean
        self.output['il_mean'] = ilmean
        self.output['op_mean'] = opmean
        self.output['ip_mean'] = ipmean

        self.runs = runs

    def getTrexOutput(self):
        return self.runs

    def getRequestedTxRate(self):
        return self.output['requested_tx_rate']

    def getAverageDR(self):
        return self.output['dl_mean']
    def getAverageOlMean(self):
        return self.output['ol_mean']
    def getAverageIlMean(self):
        return self.output['il_mean']
    def getAverageIpMean(self):
        return self.output['ip_mean']
    def getAverageOpMean(self):
        return self.output['op_mean']

 
 
 
 
    def getStdDR(self):
        return self.output['dl_std']

    def toDictionary(self):
        # We create a copy of the current dictionary in order to add the 'runs'
        # field without altering the original structure.
        s = self.output.copy()
        s['runs'] = []

        for run in self.runs:
            dict = run.toDictionary()
            s['runs'].append(dict.copy())

        return s

    def toString(self):
        s = self.toDictionary()
        return str(s)

class TrexPerfDriver():

    # Caller must assure consistency of parameters before creating a new
    # instance of this class.
    def __init__(self, server, txPort, rxPort, pcap, rate, repetitions,
                 duration):
        self.server = server
        self.txPort = txPort
        self.rxPort = rxPort
        self.pcap = pcap
        self.rate = rate
        self.repetitions = repetitions
        self.duration = duration

    def doPerformanceTest(self):
        results = []

        # We initialize the TrexDriver used to drive multiple tests with the 
        # same traffic rate.
        driver = TrexDriver(self.server, self.txPort, self.rxPort, self.pcap,
                            self.rate, self.duration)

        # Here we consider an additional run, the warm-up one. It is used to
        # warm up caches for reaching better and more stable results.
        for i in range(1 + self.repetitions):
            output = driver.run()
            if output is None:
                print('Driver returns Gan invalid result. Please check your SUT configuration.')
                sys.exit(1)

            if i > 0:
                # We skip the warm-up run which is the first one (0).
                results.append(output)
            else:
                #print('Warm-up run skipped, it will not be considered in results.')
                pass

        # We return the results array in which we have stored the result of each
        # single test run.
        return results

    def doPostProcessing(self, results):
        # We create 'TrexPerfOutput' object which contains a reference to 
        # performed runs and aggregate measurements such as mean of DR and also
        # the std. 
        output = None

        #Requested tx rate is always the same for every run in the experiment.
        txRate = None

        # We create a numpy array in order to store checked and validate data
        dlRuns = np.array([])
        olRuns = np.array([])
        ilRuns = np.array([])
        opRuns = np.array([])
        ipRuns = np.array([])

        # We process each single result
        for i in range(len(results)):
            run = results[i]
            warn = run.getWarnings()

            if warn is not None:
                # There is a warning, so it is better to print out on screen 
                # instead of suppress it.
                print('Run ({0}) - Warning {1}'.format(i, warn))
            else:
                txTotalPackets = run.getTxTotalPackets()
                rxTotalPackets = run.getRxTotalPackets()

                # Let's check if rxTotalPacket is greater than txTotalPacket. 
                # If this is the case (due to lldp packets) we normalize the
                # number of received packets with the 'txTotalPackets' counter.
                # Anyway, if the rxTotalPackets is > rxTotalPacketsTolerance then
                # some issues occurred... and we need to skip the run in order 
                # to let the results valid.
                rxTotalPacketsTolerance = txTotalPackets + (1.0 / 1000.0) * txTotalPackets
                if rxTotalPackets > rxTotalPacketsTolerance:
                    print('Run ({0}) - Warning rxTotalPackets ({1} > {2}) exceeded the threshold. Run will be skipped.'.
                        format(i, float(rxTotalPackets),
                        float(rxTotalPacketsTolerance)))

                    continue

                # We already checked that rxTotalPacket <= txTotalPackets + 1%
                if rxTotalPackets > txTotalPackets:
                    rxTotalPackets = txTotalPackets

                # We evaluate DR
                dl = rxTotalPackets / (1.0 * txTotalPackets)
                dlRuns = np.append(dlRuns, dl)
                olRuns = np.append(olRuns, run.getTxTotalBytes())
                ilRuns = np.append(ilRuns, run.getRxTotalBytes())
                opRuns = np.append(opRuns, run.getTxTotalPackets())
                ipRuns = np.append(ipRuns, run.getRxTotalPackets())

                # We set the requested tx rate only the first time (using the first
                # run in the experiment; following runs will have the same 
                # requested tx rate.
                if txRate is None:
                    txRate = run.getRequestedTxRate()
        # End of for

        # We check if the array which contains the results is empty or not. 
        # In case of empty array something is went wrong and we must terminate
        # the measurements.
        if 0 == dlRuns.size:
            print('Warning - invalid statistics: collected data is not valid.')
            return trexPerfOutput

        # We evaluate mean and std of delivery ratios
        dlMean = np.mean(dlRuns)
        olMean = np.mean(olRuns)
        ilMean = np.mean(ilRuns)
        opMean = np.mean(opRuns)
        ipMean = np.mean(ipRuns)

        if 1 < dlRuns.size: 
            dlStd = np.std(dlRuns, ddof=1)
        else:
            dlStd = 0

        # We build the object wrapper
        output = TrexPerfOutput(results, txRate, dlMean, dlStd, olMean, ilMean,opMean, ipMean)
        return output

    # Run is reentrant and it can be called multiple times without creating
    # a new TrexPerfDriver instance.
    def run(self):
        runs = []
        output = None

        # We perform tests and retrieve back the results
        runs = self.doPerformanceTest()

        # We apply some post processing operations such as the evaluation of
        # delivery ration mean value and also the std evaluation.
        output = self.doPostProcessing(runs)
        return output

#Experiment for Trex
class TrexExperiment(Experiment):

    def __init__(self, server, txPort, rxPort, pcap, rate, repetitions, duration):
        super(Experiment, self).__init__()

        self.perfDriver = TrexPerfDriver(server, txPort, rxPort, pcap, rate, 
                                         repetitions, duration)
        self.invoked = False

    def run(self, *args):
        if self.invoked:
            raise ExperimentException('Experiment already executed, please create another one')

        # Once the Experiment has been performed it cannot be used anymore
        self.invoked = True

        output = self.perfDriver.run()
        return output

# Experiment Factory for Trex
class TrexExperimentFactory(ExperimentFactory):

    def __init__(self, server, txPort, rxPort, pcap, repetitions, duration):
        super(ExperimentFactory, self).__init__()

        self.server = server
        self.txPort = txPort
        self.rxPort = rxPort
        self.pcap = pcap

        self.repetitions = repetitions
        self.duration = duration

    def build(self, txRate):
        return TrexExperiment(self.server, self.txPort, self.rxPort, self.pcap,
                              txRate, self.repetitions, self.duration)

# Entry point used for testing
if __name__ == '__main__':
    #factory = TrexExperimentFactory('127.0.0.1', 0, 1, 
                                    #'./pcap/trex-pcap-files/srv6-end_b6_encaps-64.pcap', 
    #                                10, 20)

    duration = 10 
    factory = TrexExperimentFactory('127.0.0.1', 0, 1, 
                                    './pcap/512-2-3-64.pcap', 
                                    10, duration)

    for i in range(1000, 100000, 5000):
    #for i in range(10, 20, 1):
        experiment = factory.build(str(i))
        output = experiment.run()
        if output is None:
            print('Error, experiment cannot return an empty value.')
            sys.exit(1)

        #print('Requested Tx Rate {0}, Mean {1}, Std. {2}'.format(
        #                                             output.getRequestedTxRate(), 
        #                                             output.getAverageDR(), 
        #                                             output.getStdDR()))

        print(output.getAverageOlMean()/duration, ", ", output.getAverageIlMean()/duration, ", ", output.getAverageOpMean()/duration,",", output.getAverageIpMean()/duration,",",output.getAverageDR(),",",  output.getStdDR())
