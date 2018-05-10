package ab;

import java.net.*;
import java.io.*;
import ab.AIBirdProtocol;

public class AIBirdServer {

        public static void main(String[] args) throws IOException {
                int portNumber = 2004;
                int[] buffer = new int[6];

                if (args.length > 1) {
                        System.err.println("Usage: java -jar AIBirdServer.jar [<port number>]");
                        System.exit(1);
                } else if (args.length == 1) {
                        portNumber = Integer.parseInt(args[0]);
                }
                
                System.err.println("Server will be opened on port " + portNumber);

                try (
                        ServerSocket serverSocket = new ServerSocket(portNumber);
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
