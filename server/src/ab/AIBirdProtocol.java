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
        private int curLevel = 1;
        private int actions = 0;
        private GameState currentState = null;
        private final int[] numberOfBirds = {3, 5, 4, 4, 4, 4, 4, 4, 4, 5, 4, 4, 4, 4, 4, 5, 3, 5, 4, 5, 8};

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
                                return doScreenShot();
                        case STATE:
                                return state();
                        case MYSCORE:
                                return myScore();
                        case FULLZOOMOUT:
                                return fullZoomOut();
                        case FULLZOOMIN:
                                return fullZoomIn();
                        case RESTARTLEVEL:
                                return restartLevel();
                        case LOADLEVEL:
                                return loadLevel(theInput[0]);
                        case CARTSHOOTSAFE:
                                return cartShoot(true, theInput[0], theInput[1], theInput[2]);
                        case CARTSHOOTFAST:
                                return cartShoot(false, theInput[0], theInput[1], theInput[2]);
                        case POLARSHOOTSAFE:
                                return polarShoot(true, theInput[0], theInput[1], theInput[2]);
                        case POLARSHOOTFAST:
                                return polarShoot(false, theInput[0], theInput[1], theInput[2]);
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
                if (currentState == null) {
                        return writeInt(-1);
                }
                return writeInt(currentState.getCode());
        }

        private byte[] myScore() throws IOException {
                return writeInt(score);
        }

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
                waitUntilState(GameState.PLAYING);
                score = 0;
                actions = 0;
                return writeInt(1);
        }

        private void waitUntilState(GameState desired) {
                currentState = aRobot.getState();
                while (currentState != desired) {
                        try {
                                TimeUnit.MILLISECONDS.sleep(300);
                        } catch(InterruptedException e){
                                e.printStackTrace();
                        }
                        currentState = aRobot.getState();
                }
        }

        private byte[] loadLevel(int level) throws IOException {
                aRobot.loadLevel(level);
                waitUntilState(GameState.PLAYING);
                aRobot.click();
                score = 0;
                curLevel = level;
                actions = 0;
                return writeInt(1);
        }

        private Point findSling() {
                Vision vision = getVision();
                Rectangle sling = vision.findSling();
                if (sling == null) {
                        return new Point(-1, -1);
                }
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
                currentState = aRobot.getState();
                if (++actions >= numberOfBirds[curLevel - 1]) {
                        // No birds level is over
                        score = StateUtil.getScore(ActionRobot.proxy);
                        if (score == -1) {
                                score = old_score;
                                currentState = GameState.LOST;
                                return;
                        }
                        while (currentState == GameState.PLAYING) {
                                // wait until level ends
                                TimeUnit.MILLISECONDS.sleep(300);
                                currentState = aRobot.getState();
                                old_score = score;
                                score = StateUtil.getScore(ActionRobot.proxy);
                                if (score == -1) {
                                        score = old_score;
                                        currentState = GameState.LOST;
                                }
                        }
                        return;
                }
                // Check whether score is stable
                while (same_score_count < 4) {
                        TimeUnit.MILLISECONDS.sleep(300);
                        score = StateUtil.getScore(ActionRobot.proxy);
                        if (score == -1) {      // Lost
                                score = old_score;
                                currentState = GameState.LOST;
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
                        waitUntilState(GameState.WON);
                        score = StateUtil.getScore(ActionRobot.proxy);
                }
        }
}

