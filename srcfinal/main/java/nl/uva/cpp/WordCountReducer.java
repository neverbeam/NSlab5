package nl.uva.cpp;

import java.io.IOException;

import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.*;

public class WordCountReducer extends Reducer<Text, IntWritable, Text, DoubleWritable> {

	@Override
	public void reduce(Text key, Iterable<IntWritable> values, Context context)
			throws IOException, InterruptedException {
		int sum = 0;
        double sumsquared = 0;
		int count = 0;
		for (IntWritable val : values) {
			sum += val.get();
            sumsquared += (val.get() * val.get());
			count++;
		}
        double mean = (double)sum / count;
		context.write(key, new DoubleWritable(mean));
        context.write(key, new DoubleWritable(Math.sqrt(sumsquared / count - (mean * mean ))));
	}
}
