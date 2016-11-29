package nl.uva.cpp;

import java.io.IOException;
import java.util.StringTokenizer;

import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.*;

import  me.champeau.ld.UberLanguageDetector;
import  java.util.Properties;
import  edu.stanford.nlp.ling.CoreAnnotations;
import  edu.stanford.nlp.pipeline.Annotation;
import  edu.stanford.nlp.pipeline.StanfordCoreNLP;
import  edu.stanford.nlp.neural.rnn.RNNCoreAnnotations;
import  edu.stanford.nlp.sentiment.SentimentCoreAnnotations;
import  edu.stanford.nlp.trees.Tree;
import  edu.stanford.nlp.util.CoreMap;

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
                String  lang = UberLanguageDetector.getInstance ().detectLang(text);
                if (lang.equals("en")) {
                    IntWritable dezeint = new IntWritable(findSentiment(text));
                    word.set(token);
                    context.write(word, dezeint);
                }
            }
        }
	}

    private int findSentiment(String text) {
        Properties  props = new  Properties ();
        String parseModelPath = "englishPCFG.ser.gz";
        String sentimentModelPath = "sentiment.ser.gz";
        props.setProperty("annotators", "tokenize , ssplit , parse , sentiment");
        props.put("parse.model", parseModelPath);
        props.put("sentiment.model", sentimentModelPath);
        StanfordCoreNLP  pipeline = new  StanfordCoreNLP(props);

        int  mainSentiment = 0;
        if (text != null && text.length () > 0) {
            int  longest = 0;
            Annotation  annotation = pipeline.process(text);
            for (CoreMap  sentence : annotation.get(CoreAnnotations.SentencesAnnotation.class)) {
                // 'AnnotatedTree ' is 'SentimentAnnotatedTree ' in  newer  versions
                Tree  tree = sentence.get(SentimentCoreAnnotations.AnnotatedTree.class);
                    int  sentiment = RNNCoreAnnotations.getPredictedClass(tree);
                    String  partText = sentence.toString ();
                        if (partText.length () > longest) {
                            mainSentiment = sentiment;
                            longest = partText.length ();
                        }
            }
        }
        return  mainSentiment;
    }
}
