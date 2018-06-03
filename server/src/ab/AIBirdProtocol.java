package ab;
import java.io.*;
import java.awt.image.BufferedImage;
import java.awt.Color;
import java.awt.Point;
import java.awt.Rectangle;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.TimeUnit;
import javax.imageio.ImageIO;
import ab.other.ActionRobot;
import ab.other.Shot;
import ab.utils.StateUtil;
import ab.vision.ABObject;
import ab.vision.GameStateExtractor.GameState;
import ab.vision.Vision;
import ab.vision.VisionUtils;

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
        private final byte CLOSE = 66;
        private final double X_OFFSET = 0.5;
        private final double Y_OFFSET = 0.65;
        private final boolean DEBUG = true;
        private int score = 0;
        private final String eagleHash;

        private ActionRobot aRobot;
        // private int curLevel = 1;

        AIBirdProtocol() {
                aRobot = new ActionRobot();
                ActionRobot.GoFromMainMenuToLevelSelection();
                BufferedImage eagle = null;
                try {
                        eagle = ImageIO.read(getClass().getResource("eagle.png"));
                } catch(IOException e){
                        e.printStackTrace();
                }
                eagleHash = VisionUtils.imageDigest(eagle);
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
                        case CLOSE:
                                result = 0;
                                break;
                        case LOADLEVEL:
                                result = 1;
                                break;
                        case CARTSHOOTSAFE:
                        case CARTSHOOTFAST:
                        case POLARSHOOTSAFE:
                        case POLARSHOOTFAST:
                                result = 3;
                                break;
                        default:
                                assert false: "Unknown MID: " + mid;
                }
                return result;
        }

        public byte[] processInput(byte mid, int[] theInput) throws IOException {
                switch (mid) {
                        case DOSCREENSHOT:
                                if(DEBUG) System.out.println("screenshot");
                                return doScreenShot();
                        case STATE:
                                if(DEBUG) System.out.println("state");
                                return state();
                        case MYSCORE:
                                if(DEBUG) System.out.println("score");
                                return myScore();
                        case FULLZOOMOUT:
                                if(DEBUG) System.out.println("zo");
                                return fullZoomOut();
                        case FULLZOOMIN:
                                if(DEBUG) System.out.println("zi");
                                return fullZoomIn();
                        case RESTARTLEVEL:
                                if(DEBUG) System.out.println("retart");
                                return restartLevel();
                        case LOADLEVEL:
                                if(DEBUG) System.out.println("load");
                                return loadLevel(theInput[0]);
                        case CARTSHOOTSAFE:
                                if(DEBUG) System.out.println("cartsafe");
                                return cartShoot(true, theInput[0], theInput[1], theInput[2]);
                        case CARTSHOOTFAST:
                                if(DEBUG) System.out.println("cartfast");
                                return cartShoot(false, theInput[0], theInput[1], theInput[2]);
                        case POLARSHOOTSAFE:
                                if(DEBUG) System.out.println("polarsafe");
                                return polarShoot(true, theInput[0], theInput[1], theInput[2]);
                        case POLARSHOOTFAST:
                                if(DEBUG) System.out.println("polarfast");
                                return polarShoot(false, theInput[0], theInput[1], theInput[2]);
                        case ISLEVELOVER:
                                if(DEBUG) System.out.println("levelover");
                                return isLevelOver();
                        case CLOSE:
                                aRobot.close();
                                return writeInt(1);
                        default:
                                assert false: "Unknown MID: " + mid + ")";
                                return null;             // Never Used
                }
        }

        private byte[] writeInt(int data) throws IOException {
                ByteArrayOutputStream bos = new ByteArrayOutputStream();
                DataOutputStream dos = new DataOutputStream(bos);
                dos.writeInt(data);
                return bos.toByteArray();
        }

        private byte[] doScreenShot() throws IOException {
                BufferedImage screenshot = null;
                boolean checkedNotEagle = false;
                while (!checkedNotEagle) {
                        screenshot = ActionRobot.doScreenShot();
                        BufferedImage subimage = screenshot.getSubimage(236, 333, 30, 30);
                        String subimgHash = VisionUtils.imageDigest(subimage);
                        if (subimgHash.equals(eagleHash)) {
                                aRobot.resumeEagle();
                                ActionRobot.fullyZoomOut();
                        } else {
                                checkedNotEagle = true;
                        }
                }
                ByteArrayOutputStream bos = new ByteArrayOutputStream();
                DataOutputStream dos = new DataOutputStream(bos);
                ByteArrayOutputStream ibos = new ByteArrayOutputStream();
                ImageIO.write(screenshot, "png", ibos);
                byte[] encoded = Base64.getEncoder().encode(ibos.toByteArray());
                dos.writeInt(encoded.length);
                dos.write(encoded);
                return bos.toByteArray();
        }

        private byte[] state() throws IOException {
                GameState state = aRobot.getState();
                return writeInt(state.getCode());
        }

        private byte[] myScore() throws IOException {
                return writeInt(score);
        }

        /* private byte[] currentLevel() throws IOException {
                return writeInt(curLevel);
        } */

        private byte[] fullZoomOut() throws IOException {
               ActionRobot.fullyZoomOut(); 
               return writeInt(1);
        }

        private byte[] fullZoomIn() throws IOException {
               ActionRobot.fullyZoomIn(); 
               return writeInt(1);
        }

        private byte[] restartLevel() throws IOException {
                aRobot.restartLevel();
                score = 0;
                return writeInt(1);
        }

        private byte[] loadLevel(int level) throws IOException {
                aRobot.loadLevel(level);
                try {
                        TimeUnit.MILLISECONDS.sleep(10);
                } catch(InterruptedException e){
                        e.printStackTrace();
                }
                aRobot.click();
                score = 0;
                return writeInt(1);
        }

        private Point findSling() {
                Vision vision = getVision();
                Rectangle sling = vision.findSling();
                return getReferencePoint(sling);
        }

        private byte[] cartShoot(boolean isSafe, int dx, int dy, int tap_time) throws IOException {
                Point sling = findSling();
                while (sling.x == -1) {
                        aRobot.resume();
                        sling = findSling();
                }
                Shot shot = new Shot(sling.x, sling.y, dx, dy, 0, tap_time);
                aRobot.cFastshoot(shot);
                if (!isSafe) return writeInt(1);
                try {
                        scoreCheck();
                } finally {
                        return writeInt(1);
                }
        }
        
        private byte[] polarShoot(boolean isSafe, int r_int, int theta_int, int tap_time) throws IOException {
                double r = (double)r_int;
                double theta = Math.toRadians(((double) theta_int) / 100.0);
                int dx = Math.toIntExact(Math.round(r * Math.cos(theta) * -1));
                int dy = Math.toIntExact(Math.round(r * Math.sin(theta)));
                Point sling = findSling();
                while (sling.x == -1) {
                        aRobot.resume();
                        sling = findSling();
                }
                Shot shot = new Shot(sling.x, sling.y, dx, dy, 0, tap_time);
                aRobot.cFastshoot(shot);
                if (!isSafe) return writeInt(1);
                try {
                        scoreCheck();
                } finally {
                        return writeInt(1);
                }
        }

        private byte[] isLevelOver() throws IOException {
                GameState state = aRobot.getState();
                if (state == GameState.PLAYING) {
                        Vision vision = getVision();
                        /* get Birds
                        List<ABObject> birds = vision.findBirdsMBR();
                        if (birds.isEmpty()) {   // No birds level is over.
                                return writeInt(1);
                        } */
                        // get Pigs
                        List<ABObject> pigs = vision.findPigsMBR();
                        if (pigs.isEmpty()) {   // No pigs level is over.
                                return writeInt(1);
                        }
                        return writeInt(0);
                }
                return writeInt(1);
        }

        private Vision getVision() {
                // capture Image
                BufferedImage screenshot = ActionRobot.doScreenShot();
                // process image
                return new Vision(screenshot);
        }

        // find the reference point given the sling
        public Point getReferencePoint(Rectangle sling) {
                Point p = new Point((int)(sling.x + X_OFFSET * sling.width), (int)(sling.y + Y_OFFSET * sling.width));
                return p;
        }

        private void scoreCheck() throws InterruptedException {
                TimeUnit.SECONDS.sleep(2);
                int old_score = score;
                int same_score_count = 0;
                // Check whether score is stable
                while (same_score_count < 3) {
                        TimeUnit.MILLISECONDS.sleep(300);
                        score = StateUtil.getScore(ActionRobot.proxy);
                        if (score == -1) {      // Lost
                                score = old_score;
                                return;
                        } else if (score == old_score) {
                                ++same_score_count;
                        } else {
                                same_score_count = 0;
                        }
                        old_score = score;
                }
                // get Pigs
                if (getVision().findPigsMBR().isEmpty()) {   // No pigs level is over.
                        GameState state = aRobot.getState();
                        while (state != GameState.WON) {
                                TimeUnit.MILLISECONDS.sleep(300);
                                state = aRobot.getState();
//                              BufferedImage image = ActionRobot.doScreenShot();
//                              try {
//                                      File ss = File.createTempFile("sling-", ".png");
//                                      ImageIO.write(image, "png", ss);
//                              } catch(IOException e){
//                                      e.printStackTrace();
//                              }
                        }
                        score = StateUtil.getScore(ActionRobot.proxy);
                }
        }
}

