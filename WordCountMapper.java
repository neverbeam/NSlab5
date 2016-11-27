package nl.uva.cpp;

import java.io.IOException;
import java.util.StringTokenizer;

import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.*;

public class WordCountMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

	private final static IntWritable one = new IntWritable(1);
	private Text word = new Text();

	static enum Counters {
		INPUT_WORDS
	}

	@Override
	public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
		String line = value.toString().toLowerCase();
        String text = line.split("\nw")[1];
        StringTokenizer itr = new StringTokenizer(text);
    	int count = 0;
    	while (itr.hasMoreTokens()) {
    		// Obtain the next word.
    		String token = itr.nextToken();
            if (token.startsWith("#")) {
        		// Write (word, 1) as (key, value) in output
				Sentiment sent = new Sentiment(text, token);
        		word.set(token);
        		//context.write(word, one);
				if (sent.language().equals("en")) {
					System.out.println(sent.language());
					context.write(word, new IntWritable(sent.findSentiment()));
				}
        		// Increment a counter.
        		context.getCounter(Counters.INPUT_WORDS).increment(1);
            }
        }
	}
}

