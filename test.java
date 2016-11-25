/* Test file */

import java.io.File;
import java.io.FileNotFoundException;
import java.util.*;

public class test {
    public static void main(String[] args) {
        /* Het inlezen van een file */
            HashMap<String,Integer> hmap = new HashMap<String, Integer>();
            for (int i = 0; i < 10; i ++) {
                hmap.put("a" + (char) (97 + i), 0);
            }
            System.out.println(Arrays.asList(hmap));

            String filename, mapname = "ab";
            int filenummer = 0,smallest = 0;
            while(true) {
                filename = "output/part-r-0000" + Integer.toString(filenummer);
                File fl = new File(filename);
                try {
                    Scanner s = new Scanner(fl);
                    /* Zolang er een nieuwe regel beschikbaar is, dan inlezen.*/
                    while(s.hasNextLine()) {
                        String invoer = s.nextLine();
                        String[] splitted = invoer.split("\t");
                        if (Integer.parseInt(splitted[1]) > smallest) {
                            hmap.remove(mapname);
                            hmap.put(splitted[0], Integer.parseInt(splitted[1]));
                            smallest = Collections.min(hmap.values());
                            for( String stringy : hmap.keySet()) {
                                if (smallest == hmap.get(stringy))
                                    mapname = stringy;
                            }
                        }

                    }
                }
                catch (FileNotFoundException e) {
                    System.out.println("Last file" + filename);
                    System.out.println(Arrays.asList(hmap));
                    return;
                }
                filenummer += 1;
                if (filenummer == 10) {
                    filename = "output/part-r-000";
                }
            }
    }
}
