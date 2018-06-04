package ab;

import java.net.*;
import java.io.*;
import java.util.concurrent.TimeUnit;
import ab.AIBirdProtocol;

public class AIBirdServer {

        public static void main(String[] args) throws IOException {
                int portNumber = 2004;
                int[] buffer = new int[6];

                if (args.length > 1) {
                        System.err.println("Usage: java -jar AIBirdServer.jar [<client port number>]");
                        System.exit(1);
                } else if (args.length == 1) {
                        portNumber = Integer.parseInt(args[0]);
                }
                ServerSocket serverSocket = null;
                boolean binded = false;
                while (!binded) {
                        try {
                                serverSocket = new ServerSocket(portNumber);
                                binded = true;
                        } catch(BindException e) {
                                Runtime.getRuntime().exec(String.format("fuser -k %d/tcp", portNumber));
                                try {
                                        TimeUnit.SECONDS.sleep(1);
                                } catch (InterruptedException e1) {
                                        e1.printStackTrace();
                                }
                        }
                }
                System.err.println("Client server will be opened on port " + portNumber);
                while (true) {
                        try (
                                Socket clientSocket = serverSocket.accept();
                                OutputStream out = clientSocket.getOutputStream();
                                DataInputStream in = new DataInputStream(clientSocket.getInputStream());
                        ) {
                                AIBirdProtocol abp = new AIBirdProtocol();
                                while (true) {
                                        byte mid = in.readByte();
                                        int length = abp.numberOfIntsToReadMore(mid);
                                        for (int i = 0; i < length; i++) {
                                                buffer[i] = in.readInt();
                                        }
                                        out.write(abp.processInput(mid, buffer));
                                }
                        } catch(IOException e){
                                System.out.println("Exception caught when trying to listen on port "
                                        + portNumber + " or listening for a connection.");
                                System.out.println(e.getMessage());
                        }
                }
        }
}
