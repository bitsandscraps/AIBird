package ab;
import java.io.*;
import java.awt.image.BufferedImage;
import java.util.concurrent.TimeUnit;
import java.util.List;
import javax.imageio.ImageIO;
import ab.other.ActionRobot;
import ab.other.Shot;
import ab.utils.StateUtil;
import ab.vision.ABObject;
import ab.vision.GameStateExtractor.GameState;
import ab.vision.Vision;

public class AIBirdProtocol {
        private final byte DOSCREENSHOT = 11;
        private final byte STATE = 12;
        private final byte MYSCORE = 23;
        private final byte CARTSHOOTSAFE = 31;
        private final byte CARTSHOOTFAST = 41;
        private final byte POLARSHOOTSAFE = 32;
        private final byte POLARSHOOTFAST = 42;
        private final byte FULLZOOMOUT = 34;
        private final byte FULLZOOMIN = 35;
        private final byte LOADLEVEL = 51;
        private final byte RESTARTLEVEL = 52;
        private final byte ISLEVELOVER = 60;

        private ActionRobot aRobot;
        private int curLevel = 1;

        AIBirdProtocol() {
                System.err.println("AIBirdProtocol");
                this.aRobot = new ActionRobot();
                System.err.println("ActionRobot");
                ActionRobot.GoFromMainMenuToLevelSelection();
        }

        public int numberOfIntsToReadMore(byte mid) {
                int result = -1;
                switch (mid) {
                        case DOSCREENSHOT:
                        case STATE:
                        case MYSCORE:
                        case FULLZOOMOUT:
                        case FULLZOOMIN:
                        case RESTARTLEVEL:
                        case ISLEVELOVER:
                                result = 0;
                                break;
                        case LOADLEVEL:
                                result = 1;
                                break;
                        case CARTSHOOTSAFE:
                        case CARTSHOOTFAST:
                        case POLARSHOOTSAFE:
                        case POLARSHOOTFAST:
                                result = 6;
                                break;
                        default:
                                assert false: "Unknown MID: " + mid;
                }
                return result;
        }

        public byte[] processInput(byte mid, int[] theInput) throws IOException {
                switch (mid) {
                        case DOSCREENSHOT:
                                return doScreenShot(theInput);
                        case STATE:
                                return state(theInput);
                        case MYSCORE:
                                return myScore(theInput);
                        case FULLZOOMOUT:
                                return fullZoomOut(theInput);
                        case FULLZOOMIN:
                                return fullZoomIn(theInput);
                        case RESTARTLEVEL:
                                return restartLevel(theInput);
                        case LOADLEVEL:
                                return loadLevel(theInput);
                        case CARTSHOOTSAFE:
                                return cartShootSafe(theInput);
                        case CARTSHOOTFAST:
                                return cartShootFast(theInput);
                        case POLARSHOOTSAFE:
                                return polarShootSafe(theInput);
                        case POLARSHOOTFAST:
                                return polarShootFast(theInput);
                        case ISLEVELOVER:
                                return isLevelOver();
                        default:
                                assert false: "Unknown MID: " + mid + ")";
                                return new byte[1];
                }
        }

        private byte[] writeInt(int data) throws IOException {
                ByteArrayOutputStream bos = new ByteArrayOutputStream();
                DataOutputStream dos = new DataOutputStream(bos);
                dos.writeInt(data);
                return bos.toByteArray();
        }

        private byte[] doScreenShot(int[] theInput) throws IOException {
                BufferedImage screenshot = ActionRobot.doScreenShot();
                ByteArrayOutputStream bos = new ByteArrayOutputStream();
                DataOutputStream dos = new DataOutputStream(bos);
                dos.writeInt(screenshot.getWidth());
                dos.writeInt(screenshot.getHeight());
                ImageIO.write(screenshot, "java", bos);
                return bos.toByteArray();
        }

        private byte[] state(int[] theInput) throws IOException {
                GameState state = aRobot.getState();
                return this.writeInt(state.getCode());
        }

        private byte[] myScore(int[] theInput) throws IOException {
                int score = StateUtil.getScore(ActionRobot.proxy);
                return this.writeInt(score);
        }

        private byte[] currentLevel(int[] theInput) throws IOException {
                return this.writeInt(this.curLevel);
        }

        private byte[] fullZoomOut(int[] theInput) throws IOException {
               ActionRobot.fullyZoomOut(); 
               return this.writeInt(1);
        }

        private byte[] fullZoomIn(int[] theInput) throws IOException {
               ActionRobot.fullyZoomIn(); 
               return this.writeInt(1);
        }

        private byte[] restartLevel(int[] theInput) throws IOException {
                aRobot.restartLevel();
                return this.writeInt(1);
        }

        private byte[] loadLevel(int[] theInput) throws IOException {
                System.out.println("loadLevel(" + theInput[0] + ")");
                aRobot.loadLevel(theInput[0]);
                return this.writeInt(1);
        }

        private byte[] cartShootSafe(int[] shotInfo) throws IOException {
                Shot shot = new Shot(shotInfo[0], shotInfo[1], shotInfo[2], shotInfo[3], shotInfo[4], shotInfo[5]);
                aRobot.cshoot(shot);
                try {
                        TimeUnit.SECONDS.sleep(15);
                } finally {
                        return this.writeInt(1);
                }
        }

        private byte[] cartShootFast(int[] shotInfo) throws IOException {
                Shot shot = new Shot(shotInfo[0], shotInfo[1], shotInfo[2], shotInfo[3], shotInfo[4], shotInfo[5]);
                aRobot.cFastshoot(shot);
                return this.writeInt(1);
        }
        
        private byte[] polarShootFast(int[] shotInfo) throws IOException {
                double r = shotInfo[2];
                double theta = Math.toDegrees(((double) shotInfo[3]) / 100.0);
                int dx = Math.toIntExact(Math.round(r * Math.cos(theta)));
                int dy = Math.toIntExact(Math.round(r * Math.sin(theta)));
                Shot shot = new Shot(shotInfo[0], shotInfo[1], dx, dy, shotInfo[4], shotInfo[5]);
                aRobot.cshoot(shot);
                return this.writeInt(1);
        }

        private byte[] polarShootSafe(int[] shotInfo) throws IOException {
                double r = shotInfo[2];
                double theta = Math.toRadians(((double) shotInfo[3]) / 100.0);
                int dx = Math.toIntExact(Math.round(r * Math.cos(theta) * -1));
                int dy = Math.toIntExact(Math.round(r * Math.sin(theta)));
                Shot shot = new Shot(shotInfo[0], shotInfo[1], dx, dy, shotInfo[4], shotInfo[5]);
                aRobot.cFastshoot(shot);
                try {
                        TimeUnit.SECONDS.sleep(15);
                } finally {
                        return this.writeInt(1);
                }
        }

        private byte[] isLevelOver() throws IOException {
                GameState state = aRobot.getState();
                if (state != GameState.PLAYING) {
                        Vision vision = getVision();
                        // get Birds
                        List<ABObject> birds = vision.findBirdsMBR();
                        if (birds.isEmpty()) {   // No birds level is over.
                                return this.writeInt(1);
                        }
                        // get Pigs
                        List<ABObject> pigs = vision.findPigsMBR();
                        if (pigs.isEmpty()) {   // No pigs level is over.
                                return this.writeInt(1);
                        }
                }
                return this.writeInt(0);
        }

        private Vision getVision() {
                // capture Image
                BufferedImage screenshot = ActionRobot.doScreenShot();
                // process image
                return new Vision(screenshot);
        }
}

