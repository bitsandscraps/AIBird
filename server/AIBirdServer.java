import java.net.*;
import java.io.*;

public class AIBirdServer {

        private static final int BUFFERSIZE = 100; 

        public static void main(String[] args) throws IOException {
                int portNumber = 2004;

                if (args.length > 1) {
                        System.err.println("Usage: java AIBirdServer [<port number>]");
                        System.exit(1);
                } else if (args.length == 1) {
                        portNumber = Integer.parseInt(args[0]);
                }

                try (
                        ServerSocket serverSocket = new ServerSocket(portNumber);
                        Socket clientSocket = serverSocket.accept();
                        PrintWriter out =
                                new PrintWriter(clientSocket.getOutputStream(), true);
                        BufferedReader in = new BufferedReader(
                                        new InputStreamReader(clientSocket.getInputStream()));
                ) {
                        byte[] inMessage, outMessage;
                        int inMessageLen;

                        inMessage = new byte[BUFFERSIZE];

                        // Initiate conversation with client
                        AIBirdProtocol abp = new AIBirdProtocol();
                        while (inMessageLen = in.read(inMessage, 0, BUFFERSIZE)) {
                                outMessage = abp.processInput(inMessage, inMessageLen);
                                out.write(outMessage);
                        }
                } catch(IOException e){
                        System.out.println("Exception caught when trying to listen on port "
                                + portNumber + " or listening for a connection.");
                        System.out.println(e.getMessage());
                }
        }
}
