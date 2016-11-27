package nl.uva.cpp;

import me.champeau.ld.UberLanguageDetector;
import java.util.Properties;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.pipeline.Annotation;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;
import edu.stanford.nlp.neural.rnn.RNNCoreAnnotations;
import edu.stanford.nlp.sentiment.SentimentCoreAnnotations;
import edu.stanford.nlp.trees.Tree;
import edu.stanford.nlp.util.CoreMap;


public class Sentiment {
	//read line which is tweet (ignore other lines)
	private String line;
	private String hashTag;
	
	public Sentiment(String text, String tag) {
		this.line = text;
		this.hashTag = tag;
	}
	public String getLine(){
		return this.line;
	}
	public String getTag() {
		return this.hashTag;
	}
	public String language() {
		return UberLanguageDetector.getInstance().detectLang(line);
	}
	public int findSentiment() {
		String text = line;
		String sentimentModelPath = "sentiment.ser.gz";
		String parseModelPath = "englishPCFG.ser.gz";
		Properties props = new Properties();
		props.setProperty("annotators", "tokenize , ssplit , parse , sentiment");
		props.put("parse.model", parseModelPath);
		props.put("sentiment.model", sentimentModelPath);
		StanfordCoreNLP pipeline = new StanfordCoreNLP(props);
		int mainSentiment = 0;

		if ( text != null && text.length() > 0) {
			int longest = 0;
			Annotation annotation = pipeline.process(text);
			for ( CoreMap sentence : annotation.get(CoreAnnotations.SentencesAnnotation.class)) {
				// ’ AnnotatedTree ’ is ’ SentimentAnnotatedTree ’ in newer versions
				Tree tree = sentence.get(SentimentCoreAnnotations.AnnotatedTree.class);
				int sentiment = RNNCoreAnnotations.getPredictedClass(tree);
				String partText = sentence.toString();
				if ( partText.length() > longest ) {
					mainSentiment = sentiment;
					longest = partText.length ();
				}
			}
		}
		return mainSentiment ;
	}

}
