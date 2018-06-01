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
        private final double X_OFFSET = 0.5;
        private final double Y_OFFSET = 0.65;
        private int score = 0;

        private ActionRobot aRobot;
        // private int curLevel = 1;

        AIBirdProtocol() {
                aRobot = new ActionRobot();
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
                                System.out.println("Screenshot");
                                return doScreenShot();
                        case STATE:
                                System.out.println("State");
                                return state();
                        case MYSCORE:
                                System.out.println("Score");
                                return myScore();
                        case FULLZOOMOUT:
                                System.out.println("Zoomout");
                                return fullZoomOut();
                        case FULLZOOMIN:
                                System.out.println("Zoomin");
                                return fullZoomIn();
                        case RESTARTLEVEL:
                                System.out.println("Restart");
                                return restartLevel();
                        case LOADLEVEL:
                                System.out.println("Loadlevel");
                                return loadLevel(theInput[0]);
                        case CARTSHOOTSAFE:
                                System.out.println("Cartshootsaf");
                                return cartShoot(true, theInput[0], theInput[1], theInput[2]);
                        case CARTSHOOTFAST:
                                System.out.println("Cartshootfst");
                                return cartShoot(false, theInput[0], theInput[1], theInput[2]);
                        case POLARSHOOTSAFE:
                                System.out.println("Partshootsafe");
                                return polarShoot(true, theInput[0], theInput[1], theInput[2]);
                        case POLARSHOOTFAST:
                                System.out.println("Partshootfst");
                                return polarShoot(false, theInput[0], theInput[1], theInput[2]);
                        case ISLEVELOVER:
                                System.out.println("Isover");
                                return isLevelOver();
                        default:
                                assert false: "Unknown MID: " + mid + ")";
                                return new byte[1];             // Never Used
                }
        }

        private byte[] writeInt(int data) throws IOException {
                ByteArrayOutputStream bos = new ByteArrayOutputStream();
                DataOutputStream dos = new DataOutputStream(bos);
                dos.writeInt(data);
                return bos.toByteArray();
        }

        private byte[] doScreenShot() throws IOException {
                BufferedImage screenshot = ActionRobot.doScreenShot();
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
                while (vision.findEagle(aRobot.eagleHash)) {
                        aRobot.resumeEagle();
                        vision = getVision();
                }
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
                                BufferedImage image = ActionRobot.doScreenShot();
                                try {
                                        File ss = File.createTempFile("sling-", ".png");
                                        ImageIO.write(image, "png", ss);
                                } catch(IOException e){
                                        e.printStackTrace();
                                }
                        }
                        score = StateUtil.getScore(ActionRobot.proxy);
                }
        }
}

