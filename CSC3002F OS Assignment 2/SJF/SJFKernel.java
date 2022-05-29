import simulator.Config;
import simulator.IODevice;
import simulator.Kernel;
import simulator.ProcessControlBlock;
//
import java.io.FileNotFoundException;
import java.io.IOException;
//
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;

public class SJFKernel implements Kernel {

    private ArrayList<ProcessControlBlock> readyQueue;

    public SJFKernel(Object... varargs) {
        this.readyQueue = new ArrayList<ProcessControlBlock>();
    }

    private ProcessControlBlock dispatch() {
        ProcessControlBlock oldProc;
        if (!readyQueue.isEmpty()) {
            int shortestJob = 0;
                for (int i = 0; i < readyQueue.size(); i++) {
                    if(readyQueue.get(i).getInstruction().getBurstRemaining()<readyQueue.get(shortestJob).getInstruction().getBurstRemaining()) {
                        shortestJob = i;
                    }
                }
            ProcessControlBlock nextProc = readyQueue.get(shortestJob);// choose shortest burst
            readyQueue.remove(shortestJob);

            oldProc = Config.getCPU().contextSwitch(nextProc);
            nextProc.setState(ProcessControlBlock.State.RUNNING);
        }
        else {
            oldProc = Config.getCPU().contextSwitch(null);
        }
        return oldProc;
    }

    public int syscall(int number, Object... varargs) {
        int result = 0;
        switch (number) {
             case MAKE_DEVICE:
                {
                    IODevice device = new IODevice((Integer)varargs[0], (String)varargs[1]);
                    Config.addDevice(device);
                }
                break;
             case EXECVE: 
                {
                    ProcessControlBlock pcb = this.loadProgram((String)varargs[0]);
                    if (pcb!=null) {
                        // Loaded successfully.
                        pcb.setPriority((Integer)varargs[1]);
                        readyQueue.add(pcb);
                        if (Config.getCPU().isIdle()) { 
                            this.dispatch(); 
                        }
                        else{
                            for (int i = 0; i < readyQueue.size(); i++) {
                                if(readyQueue.get(i).getInstruction().getBurstRemaining()<Config.getCPU().getCurrentProcess().getInstruction().getBurstRemaining()){
                                    ProcessControlBlock nextProc = readyQueue.get(i);
                                    ProcessControlBlock oldProc = Config.getCPU().contextSwitch(nextProc);
                                    nextProc.setState(ProcessControlBlock.State.RUNNING);
                                    oldProc.setState(ProcessControlBlock.State.READY);
                                    readyQueue.remove(i);
                                    readyQueue.add(oldProc);
                                }
                            }
                        }
                    }
                    else {
                        result = -1;
                    }
                }
                break;
             case IO_REQUEST: 
                {
                    ProcessControlBlock ioRequester = Config.getCPU().getCurrentProcess();
                    IODevice device = Config.getDevice((Integer)varargs[0]);
                    device.requestIO((Integer)varargs[1], ioRequester, this);
                    ioRequester.setState(ProcessControlBlock.State.WAITING);
                    dispatch();
                }
                break;
             case TERMINATE_PROCESS:
                {
                    Config.getCPU().getCurrentProcess().setState(ProcessControlBlock.State.TERMINATED);
                    ProcessControlBlock process = dispatch();
                    //process.setState(ProcessControlBlock.State.TERMINATED);
                }
                break;
             default:
                result = -1;
        }
        return result;
    }

    public void interrupt(int interruptType, Object... varargs){
        switch (interruptType) {
            case TIME_OUT:
                throw new IllegalArgumentException("FCFSKernel:interrupt("+interruptType+"...): this kernel does not support timeouts.");
            case WAKE_UP:
                ProcessControlBlock process = (ProcessControlBlock)varargs[1]; 
                process.setState(ProcessControlBlock.State.READY);
                readyQueue.add(process);
                if (Config.getCPU().isIdle()) { 
                    this.dispatch(); 
                }
                else{
                    for (int i = 0; i < readyQueue.size(); i++) {
                        if(readyQueue.get(i).getInstruction().getBurstRemaining()<Config.getCPU().getCurrentProcess().getInstruction().getBurstRemaining()){
                            ProcessControlBlock nextProc = readyQueue.get(i);
                            ProcessControlBlock oldProc = Config.getCPU().contextSwitch(nextProc);
                            nextProc.setState(ProcessControlBlock.State.RUNNING);
                            oldProc.setState(ProcessControlBlock.State.READY);
                            readyQueue.remove(i);
                            readyQueue.add(oldProc);
                        }
                    }
                }
                break;
            default:
                throw new IllegalArgumentException("FCFSKernel:interrupt("+interruptType+"...): unknown type.");
        }
    }

    private static ProcessControlBlock loadProgram(String filename) {
        try {
            return ProcessControlBlock.loadProgram(filename);
        }
        catch (FileNotFoundException fileExp) {
            throw new IllegalArgumentException("FCFSKernel: loadProgram(\""+filename+"\"): file not found.");
        }
        catch (IOException ioExp) {
            throw new IllegalArgumentException("FCFSKernel: loadProgram(\""+filename+"\"): IO error.");
        }
    }


}
