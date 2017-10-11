# -*- coding: utf-8 -*-
from __future__ import print_function
import subprocess
from collections import OrderedDict
from music21 import converter, roman, key
import os
import math
import numpy as np
import fractions
import itertools

# https://github.com/davidnalesnik/lilypond-roman-numeral-tool
# http://lsr.di.unimi.it/LSR/Snippet?id=710
roman_include = r"""
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% A function to create Roman numerals for harmonic analysis.
%%
%% Syntax: \markup \rN { ...list of symbols... }
%%
%% List symbols in this order (as needed): Roman numeral (or note name),
%% quality, inversion figures from top to bottom, "/" (if a secondary
%% function), Roman numeral (or note name).  Usually, you can skip unnecessary
%% items, though a spacer may be needed in some cases.  Use "" instead of the
%% initial symbol to start with the quality or inversion, for example.  Elements
%% must be separated by whitespace.
%%
%% Notenames are represented by their English LilyPond names.  In addition, you
%% may capitalize the name for a capitalized note name.
%%
%% Preceding a string representing a Roman numeral with English alterations
%% (f, flat, s, sharp, ff, flatflat, ss, x, sharpsharp, natural)
%% will attach accidentals, for example, "fVII" -> flat VII; "sharpvi" -> sharp vi.
%% You may precede inversion numbers with alterations, though "+" is not
%% presently supported.
%%
%% Qualities: use "o" for diminished, "h" for half-diminished, "+" for augmented,
%% and "f" for flat.  Other indications are possible such as combinations of "M"
%% and "m" (M, m, MM7, Mm, mm, Mmm9, etc.); add, add6, etc.
%%
%% To scale all numerals: \override  LyricText #'font-size = #2
%% or \override  TextScript #'font-size = #2
%% To scale individual numerals: \markup \override #'(font-size . 2) \rN { ... }
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% THE APPROACH %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% In our approach, a Roman numeral consists of

%% 1. A "base".  OPTIONAL. This may be a Roman numeral (some combination of I, i, V,
%% and v, unenforced); a note name; or some other string.  Roman numerals may be
%% preceded by an accidental, and a note name may be followed by one.

%% 2. a quality indicator.  OPTIONAL.  Eventually, this will simply be something to
%% set as a superscript following the base, whether or not it is actually a
%% indicator of quality.

%% 3. A single inversion number, or more than one, to be set as a column.  OPTIONAL.
%% An initial accidental is supported.  (This will be extended to "anything you want
%% to appear in a column after the quality indicator.")

%% 4. "/" followed by a "secondary base" for indicating tonicization.  OPTIONAL.
%% As with 1. this may a Roman numeral or note name, and may include an accidental.

%% The input syntax is chosen to be friendly to the user rather than the computer.
%% In particular, the user usually need only type the symbols needed when
%% reading the analytical symbol aloud.  This is not perfect: spacers
%% may be necessary for omissions.  Additionally, we try to interpret symbols
%% without requiring extra semantic indicators: i.e., figure out whether a string
%% represents a Roman numeral or a note name without the user adding an extra sign.
%% In the future, indicators might prove necessary to resolve ambiguity: along with
%% a flag to distinguish Roman numeral from note name, braces to enclose inversion
%% figures may be useful.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% INPUT FORMATTING %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% The user's input is available as a list of strings.  Here we convert this
%% list into a nested list which describes the structure of the input.

#(define (split-list symbols splitter-list)
   "Split a list of strings by a splitter which is a member of a list of
potential splitters.  The splitter may be alone or part of a string.
input is split into
@code{(( ...strings up to splitter... ) ( ...strings beginning with splitter... ))}
This function is Used to split notation for secondary chords and to isolate
inversion numbers."
   (let loop ((sym symbols) (result '()))
     (cond
      ((or (null? sym)
           (find (lambda (y) (string-contains (car sym) y)) splitter-list))
       (list (reverse result) sym))
      (else (loop (cdr sym) (cons (car sym) result))))))

#(define numbers '("2" "3" "4" "5" "6" "7" "8" "9" "11" "13"))

#(define qualities
   ;; only to allow omission of base when quality is alone
   ;; TODO--combinations of M and m, add, ADD . . .
   '("o" "+" "h"))

#(define (base-and-quality arg)
   (let ((len (length arg)))
     (cond
      ((= 0 len) '(() ()))
      ((= 1 len)
       (if (find (lambda (y) (string= (car arg) y)) qualities)
           (list '() (list (car arg)))
           (list (list (car arg)) '()))) ;; TODO figure out which is given
      ((= 2 len) (list (list (car arg)) (cdr arg))))))

#(define (base-quality-figures symbols)
   ;; given (vii o 4 3) --> ((vii o) (4 3)) --> ((vii) (o) (4 3))
   ;; (4 3) --> (() (4 3)) --> (() () (4 3))
   ;; () --> (() ()) --> (() () ())
   (let* ((split-by-numbers (split-list symbols numbers))
          (b-and-q (base-and-quality (car split-by-numbers))))
     (append b-and-q (cdr split-by-numbers))))

#(define (parse-input input)
   (let (;; (vii o 4 3 / ii) --> ((vii o 4 3) (/ ii))
          (split (split-list input '("/"))))
     ;; --> ( ((vii) (o) (4 3)) (/ ii) )
     (append
      (list (base-quality-figures (car split)))
      (cdr split))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%% NOTE NAMES / ACCIDENTALS %%%%%%%%%%%%%%%%%%%%%%%%%%

%% Formatting the input into interpretable lists continues here.  We are now
%% concerned with distinguishing Roman numerals from note names, and with representing
%% the presence and position of accidentals.

%% If a string belongs to the list of possible English notenames, we assume that
%% it is a note name.  The note name will be typeset as uppercase or lowercase depending
%% on the capitalization of the input string.

%% If a string is not a note name, we look for an alteration prefix, never a suffix.

%% The procedure parse-string-with-accidental breaks a string into a list representing
%% initial/terminal alterations and what is left.

%% Notenames and names of accidentals are based on English names.  Other
%% languages may be used by adding variables modeled after english-note names and
%% english-alterations, and changing the definitions of note names and alterations to
%% point to these new variables.

#(define english-note-names
   (map (lambda (p) (symbol->string (car p)))
     (assoc-get 'english language-pitch-names)))

#(define note-names english-note-names)

#(define (note-name? str)
   (let ((lowercased (format #f "~(~a~)" str)))
     (list? (member lowercased note-names))))

%% Groupings sharing an initial character are arranged in descending length so there
%% is no need to search for longest match in parse-string-with-accidental.
#(define english-alterations
   '("flatflat" "flat" "ff" "f"
      "sharpsharp" "sharp" "ss" "s" "x"
      "natural" "n"))

#(define alterations english-alterations)

#(define (parse-note-name str)
   "Given a note name, return a list consisting of the general name followed by
the alteration or @code{#f} if none."
   (let* ((first-char (string-take str 1))
          (all-but-first (string-drop str 1))
          (all-but-first (if (string-prefix? "-" all-but-first)
                             (string-drop all-but-first 1)
                             all-but-first))
          (all-but-first (if (string-null? all-but-first) #f all-but-first)))
     (list first-char all-but-first)))

#(define (parse-string-with-accidental str)
   "Given @var{str}, return a list in this format: (initial-accidental?
note-name-or-figure-or-RN terminal-accidental?) If an accidental is found, include
its string, otherwise @code{#t}."
   (if (not (string-null? str))
       (if (note-name? str)
           (cons #f (parse-note-name str))
           ;; Is it a Roman numeral or figure preceded (or followed) by an accidental?
           (let* ((accidental-prefix
                   (find (lambda (s) (string-prefix? s str)) alterations))
                  (accidental-suffix
                   (find (lambda (s) (string-suffix? s str)) alterations))
                  (rest (cond
                         (accidental-prefix
                          (string-drop str (string-length accidental-prefix)))
                         (accidental-suffix
                          (string-drop-right str (string-length accidental-suffix)))
                         (else str))))
             (list accidental-prefix rest accidental-suffix)))))
%{
#(define (inversion? str)
   "Check to see if a string contains a digit.  If so, it is an inversion figure."
   (not (char-set=
         char-set:empty
         (char-set-intersection (string->char-set str) char-set:digit))))
%}

%% We need to add extra space after certain characters in the default LilyPond
%% font to avoid overlaps with characters that follow.  Several of these kernings
%% don't seem to be necessary anymore, and have been commented out.
#(define (get-extra-kerning arg)
   (let ((last-char (string-take-right arg 1)))
     (cond
      ((string= last-char "V") 0.1)
      ((string= last-char "f") 0.2)
      ;((string= last-char "s") 0.2) ; sharp
      ;((string= last-char "x") 0.2) ; double-sharp
      ;((string= last-char "ss") 0.2) ; double-sharp
      (else 0.0))))

%% Create accidentals with appropriate vertical positioning.
#(define make-accidental-markup
   `(("f" . ,(make-general-align-markup Y DOWN (make-flat-markup)))
     ("flat" . ,(make-general-align-markup Y DOWN (make-flat-markup)))
     ("ff" . ,(make-general-align-markup Y DOWN (make-doubleflat-markup)))
     ("flatflat" . ,(make-general-align-markup Y DOWN (make-doubleflat-markup)))
     ("s" . ,(make-general-align-markup Y -0.6 (make-sharp-markup)))
     ("sharp" . ,(make-general-align-markup Y -0.6 (make-sharp-markup)))
     ("ss" . ,(make-general-align-markup Y DOWN (make-doublesharp-markup)))
     ("x" . ,(make-general-align-markup Y DOWN (make-doublesharp-markup)))
     ("sharpsharp" . ,(make-general-align-markup Y DOWN (make-doublesharp-markup)))
     ("n" . ,(make-general-align-markup Y -0.6 (make-natural-markup)))
     ("natural" . ,(make-general-align-markup Y -0.6 (make-natural-markup)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% BASE MARKUP %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (make-base-markup base scaling-factor)
   (let* ((base-list (parse-string-with-accidental base))
          (init-acc (first base-list))
          (end-acc (last base-list))
          (extra-space-right (get-extra-kerning (second base-list))))
     (cond
      (init-acc
       (make-concat-markup
        (list
         (make-fontsize-markup -3
           (assoc-ref make-accidental-markup init-acc))
         (make-hspace-markup (* 0.2 scaling-factor))
         (second base-list))))
      (end-acc
       (make-concat-markup
        (list
         (second base-list)
         (make-hspace-markup (* (+ 0.2 extra-space-right) scaling-factor))
         (make-fontsize-markup -3
           (assoc-ref make-accidental-markup end-acc)))))
      (else
       (if (> extra-space-right 0.0)
           (make-concat-markup
            (list
             base
             (make-hspace-markup (* extra-space-right scaling-factor))))
           base)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% QUALITY %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Symbols representing diminished, half-diminished, and augmented qualities are
%% drawn to rest atop of baseline (alignment direction = DOWN), and moved by
%% make-quality-markup to their final vertical position.  They are tailored to
%% the font-size (-3) of the ultimate caller (\rN -- default font-size = 1).

%% These symbols are drawn from scratch to allow for customization.  should we
%% simply use symbols from a font?

#(define (make-diminished-markup font-size)
   "Create circle markup for diminished quality."
   (let* ((scaling-factor (magstep font-size))
          (r (* 0.48 scaling-factor))
          (th (* 0.1 scaling-factor)))
     (make-translate-markup
      (cons r r)
      (make-draw-circle-markup r th #f))))

#(define (make-half-diminished-markup font-size)
   "Create slashed circle markup for half-diminished quality."
   (let* ((scaling-factor (magstep font-size))
          (x (* 0.56 scaling-factor))
          (y (* 0.56 scaling-factor))
          (r (* 0.48 scaling-factor))
          (th (* 0.1 scaling-factor)))
     (make-translate-markup
      (cons x y)
      (make-combine-markup
       (make-draw-circle-markup r th #f)
       (make-override-markup `(thickness . ,scaling-factor)
         (make-combine-markup
          (make-draw-line-markup (cons (- x) (- y)))
          (make-draw-line-markup (cons x y))))))))

% Noticeably thinner than "+" from font -- change?
#(define (make-augmented-markup font-size)
   "Create cross markup for augmented quality."
   (let* ((scaling-factor (magstep font-size))
          (x (* 0.56 scaling-factor))
          (y (* 0.56 scaling-factor)))
     (make-override-markup `(thickness . ,scaling-factor)
       (make-translate-markup (cons x y)
         (make-combine-markup
          (make-combine-markup
           (make-draw-line-markup (cons (- x) 0))
           (make-draw-line-markup (cons 0 (- y))))
          (make-combine-markup
           (make-draw-line-markup (cons x 0))
           (make-draw-line-markup (cons 0 y))))))))

%% TODO: more "science" in the vertical position of quality markers.
#(define (make-quality-markup quality font-size offset)
   (cond
    ;; The quantity 'offset' by itself will cause symbol to rest on the midline.  We
    ;; enlarge offset so that the symbol will be more centered alongside a possible
    ;; figure.  (Topmost figure rests on midline.)
    ((string= quality "o") (make-raise-markup (* offset 1.25) (make-diminished-markup font-size)))
    ((string= quality "h") (make-raise-markup (* offset 1.25) (make-half-diminished-markup font-size)))
    ((string= quality "+") (make-raise-markup (* offset 1.25) (make-augmented-markup font-size)))
    (else (make-raise-markup offset (make-fontsize-markup font-size quality)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% FIGURES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (make-figure-markup font-size)
   `(("f" . ,(make-general-align-markup Y DOWN
               (make-fontsize-markup font-size (make-flat-markup))))
     ("ff" . ,(make-general-align-markup Y DOWN
               (make-fontsize-markup font-size (make-doubleflat-markup))))
     ("flat" . ,(make-general-align-markup Y DOWN
                  (make-fontsize-markup font-size (make-flat-markup))))
     ("flatflat" . ,(make-general-align-markup Y DOWN
               (make-fontsize-markup font-size (make-doubleflat-markup))))
     ("s" . ,(make-general-align-markup Y -0.6
               (make-fontsize-markup font-size (make-sharp-markup))))
     ("x" . ,(make-general-align-markup Y -1.9
               (make-fontsize-markup font-size (make-doublesharp-markup))))
     ("ss" . ,(make-general-align-markup Y -1.9
               (make-fontsize-markup font-size (make-doublesharp-markup))))
     ("sharp" . ,(make-general-align-markup Y -0.6
                   (make-fontsize-markup font-size (make-sharp-markup))))
     ("sharpsharp" . ,(make-general-align-markup Y -1.9
               (make-fontsize-markup font-size (make-doublesharp-markup))))
     ("+" . ,(make-general-align-markup Y -1.5 (make-augmented-markup (+ font-size 2))))
     ("n" . ,(make-general-align-markup Y -0.6
               (make-fontsize-markup font-size (make-natural-markup))))
     ("natural" . ,(make-general-align-markup Y -0.6
                     (make-fontsize-markup font-size (make-natural-markup))))
     ))

#(use-modules (ice-9 regex))

#(define (hyphen-to-en-dash str)
   (string-regexp-substitute "-" "â" str))

%% Regular expression for splitting figure strings into words, digits, and connector characters.
#(define figure-regexp (make-regexp "[[:alpha:]]+|[[:digit:]]+|[^[:alnum:]]+"))

#(define (format-figures figures font-size)
   (let ((scaling-factor (magstep font-size)))
     (map (lambda (fig)
            (let* ((parsed-fig (map match:substring (list-matches figure-regexp fig)))
                   ;; Conversion causes character encoding problem with Frescobaldi
                   ;; if done before applying regexp
                   (parsed-fig (map hyphen-to-en-dash parsed-fig)))
              (reduce
               (lambda (elem prev) (make-concat-markup (list prev elem)))
               empty-markup
               (map (lambda (f)
                      (let ((alteration
                             (assoc-ref (make-figure-markup (- font-size 2)) f)))
                        (make-concat-markup
                         (list
                          (if alteration alteration (make-fontsize-markup font-size f))
                          ;; TODO: don't add space at the end
                          (make-hspace-markup (* 0.2 scaling-factor))))))
                 parsed-fig))))
       figures)))

#(define (make-figures-markup figures font-size offset)
   ;; Without offset the column of figures would be positioned such that the
   ;; topmost figure rests on the baseline. Adding offset causes the upper figure
   ;; to rest on the midline of base.
   (let ((formatted-figures (format-figures figures -3)))
     (make-override-markup `(baseline-skip . ,(* 1.4 (magstep font-size)))
       (make-raise-markup offset
         (make-right-column-markup formatted-figures)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SECONDARY RN %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (make-secondary-markup second-part scaling-factor)
   (make-concat-markup
    (list
     (car second-part)
     (if (string-null? (cadr second-part))
         empty-markup
         (make-concat-markup
          (list
           (make-hspace-markup (* 0.2 scaling-factor))
           (if (car (parse-string-with-accidental (cadr second-part)))
               (make-hspace-markup (* 0.2 scaling-factor))
               empty-markup)
           (make-base-markup (cadr second-part) scaling-factor)))))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SYNTHESIS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define-markup-command (rN layout props symbols) (markup-list?)
   #:properties ((font-size 1))
   "Create a symbol for Roman numeral analysis from a @var{symbols}, a list
of strings."
   (let* ((parsed-input (parse-input symbols))
          (first-part (car parsed-input))
          (second-part (cadr parsed-input)) ; slash and what follows
          (base (car first-part))
          (quality (cadr first-part))
          (figures (caddr first-part))
          ;; A multiplier for scaling quantities measured in staff-spaces to
          ;; reflect font-size delta.  Spacing between elements is currently
          ;; controlled by the magstep of the rN font-size.
          (scaling-factor (magstep font-size))
          (base-markup
           (if (or (null? base) (string-null? (car base))) ; "" used as spacer
               #f
               (make-base-markup (car base) scaling-factor)))
          ;; The height of figures and quality determined by midline of base.  If
          ;; there is no base, use forward slash as a representative character.
          (dy (* 0.5
                (interval-length
                 (ly:stencil-extent
                  (interpret-markup
                   layout props (if (markup? base-markup)
                                    base-markup "/"))
                  Y))))
          (quality-markup
           (if (null? quality)
               #f
               (make-concat-markup
                (list
                 (make-hspace-markup (* 0.1 scaling-factor))
                 (make-quality-markup (car quality) -3 dy)))))
          (figures-markup
           (if (null? figures)
               #f
               (make-concat-markup
                (list (make-hspace-markup (* 0.1 scaling-factor))
                  (make-figures-markup figures font-size dy)))))
          (secondary-markup
           (if (null? second-part)
               #f
               (make-concat-markup
                (list
                 (if (= (length figures) 1)
                     ;; allows slash to tuck under if single figure
                     (make-hspace-markup (* -0.2 scaling-factor))
                     ;; slightly more space given to slash
                     (make-hspace-markup (* 0.2 scaling-factor)))
                 (make-secondary-markup second-part scaling-factor)))))
          (visible-markups
           (filter markup?
                   (list base-markup quality-markup figures-markup secondary-markup))))
     (interpret-markup layout props
       (make-concat-markup visible-markups))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% KEY INDICATIONS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define-markup-command (keyIndication layout props arg) (markup?)
   #:properties ((font-size 1))
   "Create a key indicator consisting of a English note name followed by a
colon.  Whitespace after the note name will be included in the returned markup."
   (let* ((scaling-factor (magstep font-size))
          (divide-at-spaces (string-match "([^[:space:]]+)([[:space:]]+)$" arg))
          (base (if divide-at-spaces
                    (match:substring divide-at-spaces 1)
                    arg))
          (trailing-spaces (if divide-at-spaces
                               (match:substring divide-at-spaces 2)
                               empty-markup)))
     (interpret-markup layout props
       (make-concat-markup
        (list
         (make-base-markup base scaling-factor)
         (make-hspace-markup (* 0.2 scaling-factor))
         ":"
         trailing-spaces)))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SCALE DEGREES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#(define (parse-scale-degree str alteration-list)
   "Given @var{str}, return a list in this format: (name-of-alteration-or-#f degree)."
   (if (not (string-null? str))
       (let* ((alteration
               (find (lambda (s) (string-prefix? s str)) alteration-list))
              (rest (if alteration
                        (string-drop str (string-length alteration))
                        str)))
         (list alteration rest))))

#(define (hat font-size)
   "Draw a caret for use with scale degrees."
   (let* ((scaling-factor (magstep font-size))
          (x (* 0.25 scaling-factor))
          (y x)
          (th scaling-factor))
     (make-override-markup `(thickness . ,th)
       (make-combine-markup
        (make-draw-line-markup (cons x y))
        (make-translate-markup (cons x y)
          (make-draw-line-markup (cons x (- y))))))))

#(define-markup-command (scaleDegree layout props degree) (markup?)
   #:properties ((font-size 1))
   "Return a digit topped by a caret to represent a scale degree.  Alterations may
be added by prefacing @var{degree} with an English alteration."
   (let* ((scale-factor (magstep font-size))
          (caret (hat font-size))
          (degree-list (parse-scale-degree degree english-alterations))
          (alteration (car degree-list))
          (number (cadr degree-list))
          (alteration-markup (assoc-ref make-accidental-markup alteration))
          (alteration-markup
           (if alteration-markup
               (make-fontsize-markup -3 alteration-markup)
               alteration-markup))
          (number-and-caret
           (make-general-align-markup Y DOWN
             (make-override-markup `(baseline-skip . ,(* 1.7 scale-factor))
               (make-center-column-markup
                (list
                 caret
                 number))))))
     (interpret-markup layout props
       (if alteration-markup
           (make-concat-markup (list
                                alteration-markup
                                number-and-caret))
           number-and-caret))))
"""

# Convenience function to reuse the defined env
def pwrap(args, shell=False):
    p = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    return p

# Print output
# http://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
def execute(cmd, shell=False):
    popen = pwrap(cmd, shell=shell)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def pe(cmd, shell=True):
    """
    Print and execute command on system
    """
    ret = []
    for line in execute(cmd, shell=shell):
        ret.append(line)
        print(line, end="")
    return ret


def music21_extract(p):
    """
    Taken from pthbldr

    Takes in a Music21 score, and outputs dict
    """
    parts = []
    parts_times = []
    parts_delta_times = []
    parts_extras = []
    parts_time_signatures = []
    parts_key_signatures = []
    c = p.chordify()
    ks = p.parts[0].stream().flat.keySignature
    parts_roman_chords = []
    parts_chords = []
    for this_chord in c.recurse().getElementsByClass('Chord'):
        parts_chords.append(this_chord.fullName)
        #print(this_chord.measureNumber, this_chord.beatStr, this_chord)
        rn = roman.romanNumeralFromChord(this_chord, ks.asKey())
        parts_roman_chords.append(rn.figure)

    for i, pi in enumerate(p.parts):
        part = []
        part_time = []
        part_delta_time = []
        part_extras = []
        total_time = 0
        ts = pi.stream().flat.timeSignature
        ks = pi.stream().flat.keySignature
        if len(ks.alteredPitches) == 0:
            parts_key_signatures.append([0])
        else:
            parts_key_signatures.append([ks.sharps])
        parts_time_signatures.append((ts.numerator, ts.denominator))
        for n in pi.stream().flat.notesAndRests:
            if n.isRest:
                part.append(0)
            else:
                try:
                    part.append(n.midi)
                except AttributeError:
                    continue
            if n.tie is not None:
                if n.tie.type == "start":
                    part_extras.append(1)
                elif n.tie.type == "continue":
                    part_extras.append(2)
                elif n.tie.type == "stop":
                    part_extras.append(3)
                else:
                   print("another type of tie?")
                   from IPython import embed; embed(); raise ValueError()
            elif len(n.expressions) > 0:
                print("trill or fermata?")
                from IPython import embed; embed(); raise ValueError()
            else:
                part_extras.append(0)

            part_time.append(total_time + n.duration.quarterLength)
            total_time = part_time[-1]
            part_delta_time.append(n.duration.quarterLength)
        parts.append(part)
        parts_times.append(part_time)
        parts_delta_times.append(part_delta_time)
        parts_extras.append(part_extras)
    return {"parts": parts,
            "parts_times": parts_times,
            "parts_delta_times": parts_delta_times,
            "parts_extras": parts_extras,
            "parts_time_signatures": parts_time_signatures,
            "parts_key_signatures": parts_key_signatures,
            "parts_chords": parts_chords,
            "parts_roman_chords": parts_roman_chords}


def pitch_and_duration_to_piano_roll(list_of_pitch_voices, list_of_duration_voices, min_dur):
    def expand(pitch, dur, min_dur):
        assert len(pitch) == len(dur)
        expanded = [int(d // min_dur) for d in dur]
        check = [d / min_dur for d in dur]
        assert all([e == c for e, c in zip(expanded, check)])
        stretch = [[p] * e for p, e in zip(pitch, expanded)]
        # flatten out to 1 voice
        return [pi for p in stretch for pi in p]

    res = []
    for lpv, ldv in zip(list_of_pitch_voices, list_of_duration_voices):
        qi = expand(lpv, ldv, min_dur)
        res.append(qi)

    min_len = min([len(ri) for ri in res])
    res = [ri[:min_len] for ri in res]
    piano_roll = np.array(res).transpose()
    return piano_roll


def pitches_and_durations_to_pretty_midi(pitches, durations,
                                         save_dir="samples",
                                         name_tag="sample_{}.mid",
                                         add_to_name=0,
                                         lower_pitch_limit=12,
                                         list_of_quarter_length=None,
                                         default_quarter_length=47,
                                         voice_params="woodwinds"):
    # allow list of list of list
    """
    takes in list of list of list, or list of array with axis 0 time, axis 1 voice_number (S,A,T,B)
    outer list is over samples, middle list is over voice, inner list is over time
    durations assumed to be scaled to quarter lengths e.g. 1 is 1 quarter note
    2 is a half note, etc
    """
    is_seq_of_seq = False
    try:
        pitches[0][0]
        durations[0][0]
        if not hasattr(pitches, "flatten") and not hasattr(durations, "flatten"):
            is_seq_of_seq = True
    except:
        raise ValueError("pitches and durations must be a list of array, or list of list of list (time, voice, pitch/duration)")

    if is_seq_of_seq:
        if hasattr(pitches[0], "flatten"):
            # it's a list of array, convert to list of list of list
            pitches = [[[pitches[i][j, k] for j in range(pitches[i].shape[0])] for k in range(pitches[i].shape[1])] for i in range(len(pitches))]
            durations = [[[durations[i][j, k] for j in range(durations[i].shape[0])] for k in range(durations[i].shape[1])] for i in range(len(durations))]


    import pretty_midi
    # BTAS mapping
    def weird():
        voice_mappings = ["Sitar", "Orchestral Harp", "Acoustic Guitar (nylon)",
                          "Pan Flute"]
        voice_velocity = [20, 80, 80, 40]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., .95]
        return voice_mappings, voice_velocity, voice_offset, voice_decay

    if voice_params == "weird":
        voice_mappings, voice_velocity, voice_offset, voice_decay = weird()
    elif voice_params == "weird_r":
        voice_mappings, voice_velocity, voice_offset, voice_decay = weird()
        voice_mappings = voice_mappings[::-1]
        voice_velocity = voice_velocity[::-1]
        voice_offset = voice_offset[::-1]
    elif voice_params == "nylon":
        voice_mappings = ["Acoustic Guitar (nylon)"] * 4
        voice_velocity = [20, 16, 25, 10]
        voice_offset = [0, 0, 0, -12]
        voice_decay = [1., 1., 1., 1.]
        voice_decay = voice_decay[::-1]
    elif voice_params == "legend":
        # LoZ
        voice_mappings = ["Acoustic Guitar (nylon)"] * 3 + ["Pan Flute"]
        voice_velocity = [20, 16, 25, 5]
        voice_offset = [0, 0, 0, -12]
        voice_decay = [1., 1., 1., .95]
    elif voice_params == "organ":
        voice_mappings = ["Church Organ"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [.98, .98, .98, .98]
    elif voice_params == "piano":
        voice_mappings = ["Acoustic Grand Piano"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "electric_piano":
        voice_mappings = ["Electric Piano 1"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "harpsichord":
        voice_mappings = ["Harpsichord"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "woodwinds":
        voice_mappings = ["Bassoon", "Clarinet", "English Horn", "Oboe"]
        voice_velocity = [50, 30, 30, 40]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    else:
        # eventually add and define dictionary support here
        raise ValueError("Unknown voice mapping specified")

    # normalize
    mm = float(max(voice_velocity))
    mi = float(min(voice_velocity))
    dynamic_range = min(80, (mm - mi))
    # keep same scale just make it louder?
    voice_velocity = [int((80 - dynamic_range) + int(v - mi)) for v in voice_velocity]

    if not is_seq_of_seq:
        order = durations.shape[-1]
    else:
        try:
            # TODO: reorganize so list of array and list of list of list work
            order = durations[0].shape[-1]
        except:
            order = len(durations[0])
    voice_mappings = voice_mappings[-order:]
    voice_velocity = voice_velocity[-order:]
    voice_offset = voice_offset[-order:]
    voice_decay = voice_decay[-order:]
    if not is_seq_of_seq:
        pitches = [pitches[:, i, :] for i in range(pitches.shape[1])]
        durations = [durations[:, i, :] for i in range(durations.shape[1])]

    n_samples = len(durations)
    for ss in range(n_samples):
        durations_ss = durations[ss]
        pitches_ss = pitches[ss]
        # same number of voices
        assert len(durations_ss) == len(pitches_ss)
        # time length match
        assert all([len(durations_ss[i]) == len(pitches_ss[i]) for i in range(len(pitches_ss))])
        pm_obj = pretty_midi.PrettyMIDI()
        # Create an Instrument instance for a cello instrument
        def mkpm(name):
            return pretty_midi.instrument_name_to_program(name)

        def mki(p):
            return pretty_midi.Instrument(program=p)

        pm_programs = [mkpm(n) for n in voice_mappings]
        pm_instruments = [mki(p) for p in pm_programs]

        if list_of_quarter_length is None:
            # qpm to s per quarter = 60 s per min / quarters per min
            time_scale = 60. / default_quarter_length
        else:
            time_scale = 60. / list_of_quarter_length[ss]

        time_offset = np.zeros((order,))

        # swap so that SATB order becomes BTAS for voice matching
        pitches_ss = pitches_ss[::-1]
        durations_ss = durations_ss[::-1]

        # time
        for ii in range(len(durations_ss[0])):
            # voice
            for jj in range(order):
                try:
                    pitches_isj = pitches_ss[jj][ii]
                    durations_isj = durations_ss[jj][ii]
                except IndexError:
                    # voices may stop short
                    continue
                p = int(pitches_isj)
                d = durations_isj
                if d < 0:
                    continue
                if p < 0:
                    continue
                # hack out the whole last octave?
                s = time_scale * time_offset[jj]
                e = time_scale * (time_offset[jj] + voice_decay[jj] * d)
                time_offset[jj] += d
                if p < lower_pitch_limit:
                    continue
                note = pretty_midi.Note(velocity=voice_velocity[jj],
                                        pitch=p + voice_offset[jj],
                                        start=s, end=e)
                # Add it to our instrument
                pm_instruments[jj].notes.append(note)
        # Add the instrument to the PrettyMIDI object
        for pm_instrument in pm_instruments:
            pm_obj.instruments.append(pm_instrument)
        # Write out the MIDI data

        sv = save_dir + os.sep + name_tag.format(ss + add_to_name)
        try:
            pm_obj.write(sv)
        except ValueError:
            print("Unable to write file {} due to mido error".format(sv))


def quantized_to_pretty_midi(quantized,
                             quantized_bin_size,
                             save_dir="samples",
                             name_tag="sample_{}.mid",
                             add_to_name=0,
                             lower_pitch_limit=12,
                             list_of_quarter_length=None,
                             max_hold_bars=1,
                             default_quarter_length=47,
                             voice_params="woodwinds"):
    """
    takes in list of list of list, or list of array with axis 0 time, axis 1 voice_number (S,A,T,B)
    outer list is over samples, middle list is over voice, inner list is over time
    """

    is_seq_of_seq = False
    try:
        quantized[0][0]
        if not hasattr(quantized[0], "flatten"):
            is_seq_of_seq = True
    except:
        try:
            quantized[0].shape
        except AttributeError:
            raise ValueError("quantized must be a sequence of sequence (such as list of array, or list of list) or numpy array")

    # list of list or mb?
    n_samples = len(quantized)
    all_pitches = []
    all_durations = []

    max_hold = int(max_hold_bars / quantized_bin_size)
    if max_hold < max_hold_bars:
        max_hold = max_hold_bars

    for ss in range(n_samples):
        pitches = []
        durations = []
        if is_seq_of_seq:
            voices = len(quantized[ss])
            qq = quantized[ss]
        else:
            voices = quantized[ss].shape[1]
            qq = quantized[ss].T


        for i in range(voices):
            q = qq[i]
            pitch_i = [0]
            dur_i = []
            cur = 0
            count = 0
            for qi in q:
                if qi != cur:# or count > max_hold:
                    pitch_i.append(qi)
                    quarter_count = quantized_bin_size * (count + 1)
                    dur_i.append(quarter_count)
                    cur = qi
                    count = 0
                else:
                    count += 1
            quarter_count = quantized_bin_size * (count + 1)
            dur_i.append(quarter_count)
            pitches.append(pitch_i)
            durations.append(dur_i)
        all_pitches.append(pitches)
        all_durations.append(durations)
    pitches_and_durations_to_pretty_midi(all_pitches, all_durations,
                                         save_dir=save_dir,
                                         name_tag=name_tag,
                                         add_to_name=add_to_name,
                                         lower_pitch_limit=lower_pitch_limit,
                                         list_of_quarter_length=list_of_quarter_length,
                                         default_quarter_length=default_quarter_length,
                                         voice_params=voice_params)


# rough guide https://www.python-course.eu/python_scores.php
def plot_lilypond(upper_voices, lower_voices=None, own_staves=False,
                  key_signatures=None,
                  time_signatures=None,
                  chord_annotations=None,
                  interval_figures=None,
                  use_clefs=None,
                  fpath="tmp.ly",
                  title="Tmp", composer="Tmperstein", tagline="Copyright:?",
                  x_zoom_bounds=(90, 780), y_zoom_bounds=(50, 220)):
    """
    Expects upper_voices and lower_voices to be list of list

    Needs lilypond, and pdf2svg installed (sudo apt-get install pdf2svg)
    """
    if len(upper_voices) > 1:
        if lower_voices == None and own_staves==False:
            raise ValueError("Multiple voices in upper staff with own_staves=False")
    if use_clefs is None:
        use_clefs = ["treble" for i in range(len(pitches))]
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    # need to align them for chord write T_T
    # for now assume 4/4
    pre = '\\version "2.12.3"'
    pre += roman_include
    minus_keys_flats = ["b", "e", "a", "d", "g", "c", "f"]
    minus_keys_names = ["\key f \major", "\key g \minor",  "\key c \minor",
                        "\key f \minor", "\key bes \minor", "\key ees \minor",
                        "\key aes \minor"]
    minus_keys_flats = minus_keys_flats[::-1]
    minus_keys_names = minus_keys_names[::-1]
    plus_keys_sharps = ["f", "c", "g", "d", "a", "e", "b"]
    plus_keys_names = ["\key g \major", "\key d \major",  "\key a \major",
                       "\key e \major", "\key b \major", "\key fis \major",
                       "\key cis \major"]
    trange = len(upper_voices)
    if lower_voices is not None:
        trange += len(lower_voices)
    if key_signatures is None:
        key_signatures = [[0] for i in range(trange)]
    if time_signatures is None:
        time_signatures = [(4, 1) for i in range(trange)]
    assert len(key_signatures) == trange
    assert len(time_signatures) == trange
    chord_str_pre = """\nanalysis = \lyricmode {
    % \set stanza  = #"G:"
  % For bare Roman numerals, \\rN simply outputs the string."""
    chord_str_post = "\n}\n"
    # this is fake test data
    '''
    chords = """
      \markup \\rN { I }
      I
      \markup \\rN { V 6 5 }
      \markup \\rN { vii o 4 3 / IV }
      \markup \\rN { IV 6 }
      \markup \\rN { ii h 4 3 }
      \markup \\rN { Fr +6 }
      \markup \\rN { I 6 4 }
      \markup \\rN { vii o 7 / vi }
      vi
    """
    '''
    # parse chord annotations
    if chord_annotations is None:
        chord_str = chord_str_pre + chord_str_post
    else:
        chords = ""
        lily_chords = map_music21_romans_to_lilypond(chord_annotations)
        chord_template_pre = "\markup \\rN { "
        chord_template_post = " }\n"
        for n, lc in enumerate(lily_chords):
            if len(lc.strip()) == 1:
                chord_template = lc + "\n"
            else:
                chord_template = chord_template_pre + lc + chord_template_post
            chords += chord_template
            # need to double the first element due to rendering issues in lilypond
            if n == 0:
                chords += chord_template
        chord_str = chord_str_pre + chords + chord_str_post
        chord_str += ""

    pre += chord_str

    if own_staves == False:
        raise ValueError("FIX")
        upper_staff = ""
        lower_staff = ""

        for n, uv in enumerate(upper_voices):
            ksi = key_signatures[n][0]
            tsi = time_signatures[n]
            if ksi != 0:
                if ksi < 0:
                    key_name = minus_keys_names[ksi]
                else:
                    assert ksi - 1 >= 0
                    key_name = plus_keys_names[ksi - 1]
                upper_staff += key_name + " "
                upper_staff += "\\time {}/{}".format(tsi[0], tsi[1]) + " "
            for u in uv:
                upper_staff += u + " "

        if lower_voices is not None:
            for n, lv in lower_voices:
                n_offset = n + len(upper_voices)
                ksi = key_signatures[n_offset][0]
                tsi = time_signatures[n_offset]
                if ksi != 0:
                    if ksi < 0:
                        key_name = minus_keys_names[ksi]
                    else:
                        assert ksi - 1 >= 0
                        key_name = plus_keys_names[ksi - 1]
                    lower_staff += key_name + " "
                    lower_staff += "\\time {}/{}".format(tsi[0], tsi[1]) + " "
                for l in lv:
                    lower_staff += l + " "

        staff = "{\n\\new PianoStaff << \n"
        staff += "  \\new Staff {" + upper_staff + "}\n"
        if lower_staff != "":
            staff += "  \\new Staff { \clef bass " + lower_staff + "}\n"
        staff += ">>\n}\n"
        raise ValueError("upper/lower voice not handled yet")
    else:
        if lower_voices is not None:
            raise ValueError("Put all voices into list of list upper_voices!")
        staff = "{\n\\new StaffGroup << \n"
        for n, v in enumerate(upper_voices):
            this_staff = ""
            ksi = key_signatures[n][0]
            tsi = time_signatures[n]
            if ksi != 0:
                if ksi < 0:
                    key_name = minus_keys_names[ksi]
                else:
                    assert ksi - 1 >= 0
                    key_name = plus_keys_names[ksi - 1]
                this_staff += key_name + " "
                this_staff += "\\time {}/{}".format(tsi[0], tsi[1]) + " "
            for vi in v:
                this_staff += vi + " "

            this_voice = "{}".format("voice{}".format(n))
            staff += '  \\new Voice = "{}"'.format(this_voice) + " {" + '\clef "' + use_clefs[n] + '" ' + this_staff + "}\n"
            if interval_figures is not None and len(interval_figures) > n:
                this_intervals = interval_figures[n]
                intervals_str = ""
                for ti in this_intervals:
                    intervals_str += "<" + str(ti) + "> "
                intervals_str = intervals_str.strip()
                staff += "  \\new FiguredBass \\figuremode { " + intervals_str + " }\n"
            # only the bottom staff...
            if n == trange - 1:
                staff += '  \\new Lyrics \\lyricsto "{}"'.format(this_voice) + " { \\analysis }\n"
        staff += ">>\n}\n"
    title = """\header {{
title = "{}"
composer = "{}"
tagline = "{}"
}}""".format(title, composer, tagline)

    final_ly = pre + staff + title
    with open(fpath, "w") as f:
        f.write(final_ly)

    # also make the pdf?
    # pe("lilypond {}".format(fpath))
    pe("lilypond -fpng {}".format(fpath))
    if len(fpath.split(os.sep)) == 1:
        flist = os.listdir(os.getcwd())
    else:
        flist = os.listdir(str(os.sep).join(fpath.split(os.sep)[:-1]))
    valid_files_name = ".".join(fpath.split(os.sep)[-1].split(".")[:-1])
    flist = [fl for fl in flist if valid_files_name in fl]
    # hardcode to only show 1 page for now...
    flist = [fl for fl in flist if "page1" in fl or "page" not in fl]
    latest_file = max(flist, key=os.path.getctime)
    img = mpimg.imread(latest_file)
    f = plt.figure()
    ax = plt.gca()
    if None in x_zoom_bounds:
        if x_zoom_bounds[-1] is not None:
            raise ValueError("None for x_zoom_bounds only supported on last entry")
        x_zoom_bounds = (x_zoom_bounds[0], img.shape[1])

    if None in y_zoom_bounds:
        if y_zoom_bounds[-1] is not None:
            raise ValueError("None for y_zoom_bounds only supported on last entry")
        y_zoom_bounds = (y_zoom_bounds[0], img.shape[0])
    ax.set_xlim(x_zoom_bounds[0], x_zoom_bounds[1])
    ax.set_ylim(y_zoom_bounds[1], y_zoom_bounds[0])
    ax.imshow(img)
    plt.show()


def map_midi_pitches_to_lilypond(pitches, key_signatures=None):
    # takes in list of list
    # 0 = rest
    # 12 = C0
    # 24 = C1
    # 36 = C2
    # 48 = C3
    # 60 = C4
    # 72 = C5
    # 84 = C6

    # accidentals are key dependent! oy vey
    sharp_notes = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]
    flat_notes =  ["c", "des", "d", "ees", "e", "f", "ges", "g", "aes", "a", "bes", "ces"]
    octave_map = [",,,", ",,", ",", "", "'", "''", "'''"]
    minus_keys_flats = ["b", "e", "a", "d", "g", "c", "f"]
    minus_keys_flats = minus_keys_flats[::-1]
    plus_keys_sharps = ["f", "c", "g", "d", "a", "e", "b"]
    rest = "r"
    lily_str_lists = []
    if key_signatures is None:
        key_signatures = [[0] for i in range(len(pitches))]
    use_voice_notes = [sharp_notes if key_signatures[i][0] >= 0 else flat_notes
                       for i in range(len(pitches))]
    assert len(key_signatures) == len(pitches)
    for n, (ks, pv) in enumerate(zip(key_signatures, pitches)):
        use_notes = use_voice_notes[n]
        note_str = [use_notes[int(pvi % 12)] if pvi != 0 else rest for pvi in pv]
        octave_str = [octave_map[int(pvi // 12)] if pvi != 0 else "" for pvi in pv]
        str_list = [ns + os for ns, os in zip(note_str, octave_str)]
        lily_str_lists.append(str_list)
    return lily_str_lists


def map_music21_romans_to_lilypond(chord_annotations):
    #ordered long to short so first match is "best"
    #major_functions = ["I", "II", "III", "IV", "V", "VI", "VII"]
    major_functions = ["VII", "III", "VI", "IV", "II", "V", "I"]
    minor_functions = [mf.lower() for mf in major_functions]
    lilypond_chords = []
    for ca in chord_annotations:
        fca = None
        ext = None
        pre = ""
        if "#" == ca[0]:
            ca = ca[1:]
            pre += ca[0]

        # need to parse it :|
        # try major first, then minor
        if len(ca) > 1:
            for n in range(1, len(ca)):
               for maf, mif in zip(major_functions, minor_functions):
                   if ca[:n] in maf:
                       fca = "".join(ca[:n])
                       ext = " ".join([cai for cai in ca[n:]])
                       pre += ""
                       break
                   elif ca[:n] in mif:
                       fca = "".join(ca[:n])
                       ext = " ".join([cai for cai in ca[n:]])
                       pre += ""
                       break
        elif len(ca) == 1:
            # len == 1
            fca = ca
            ext = ""
            pre += ""
        else:
            print("empty chord annotation!")
            from IPython import embed; embed(); raise ValueError()

        # still no matches!
        if fca is None:
            print("wrong...")
            from IPython import embed; embed(); raise ValueError()

        if fca in major_functions:
            matches = [major_functions[n] for n, ma in enumerate(major_functions) if fca == ma]
        elif fca in minor_functions:
            matches = [minor_functions[n] for n, mi in enumerate(minor_functions) if fca == mi]
        else:
            print("???")
            from IPython import embed; embed(); raise ValueError()
        lily_chord_function = matches[0] + " " + ext
        lilypond_chords.append(lily_chord_function)
    return lilypond_chords


def map_midi_durations_to_lilypond(durations, extras=None):
    # assumed to be relative lengths from quarter note?
    # do I need to make Fraction objects?
    # default is quarter note
    def ff(f):
        return fractions.Fraction(f)

    duration_map = {ff(8.): "\\breve",
                    ff(6.): "1.",
                    ff(4.): "1",
                    ff(3.): "2.",
                    ff(2.): "2",
                    ff(1.): "4",
                    ff(.5): "8",
                    ff(.25): "16",
                    ff(.125): "32",
                    ff(.0625): "64"}

    if extras is None:
        extras = []
        for du in durations:
            e = []
            for diu in du:
                e.append(0)
            extras.append(e)

    lily_str_lists = []
    assert len(durations) == len(extras)
    for dv, ev in zip(durations, extras):
        str_list = []
        assert len(dv) == len(ev)
        for dvi, evi in zip(dv, ev):
            try:
                frac_dvi = duration_map[ff(dvi)]
                if evi != 0:
                   if evi == 1 or evi == 2:
                       frac_dvi += "~"
                str_list.append(frac_dvi)
            except KeyError:
                raise KeyError("No known mapping for duration {}".format(dvi))
        lily_str_lists.append(str_list)
    return lily_str_lists


def pitches_and_durations_to_lilypond_notation(pitches, durations, extras=None,
                                               key_signatures=None):
    lilypitches = map_midi_pitches_to_lilypond(pitches, key_signatures=key_signatures)
    lilydurs = map_midi_durations_to_lilypond(durations, extras)
    assert len(lilypitches) == len(lilydurs)
    lilycomb = []
    for lp, ld in zip(lilypitches, lilydurs):
        assert len(lp) == len(ld)
        lc = [lpi + ldi for lpi, ldi in zip(lp, ld)]
        lilycomb.append(lc)
    return lilycomb


def plot_pitches_and_durations(pitches, durations, extras=None,
                               time_signatures=None,
                               key_signatures=None,
                               chord_annotations=None,
                               interval_figures=None,
                               use_clefs=None):
    # map midi pitches to lilypond ones... oy
    voices = pitches_and_durations_to_lilypond_notation(pitches, durations, extras, key_signatures=key_signatures)
    #plot_lilypond([voices[1]])
    #plot_lilypond([voices[0]], [voices[-1]])
    #plot_lilypond([voices[0]], [voices[-1]], own_staves=True)
    # TODO: fix own_staves=False issues with conflicting time/key signatures
    # raise an error
    # down the line, fix accidentals on case by case basis :|
    # add options for chord notations, and intervals for final analysis
    # add grey notes (all possibles) as well to visualize the decoding?
    plot_lilypond(voices, own_staves=True,
                  time_signatures=time_signatures,
                  key_signatures=key_signatures,
                  chord_annotations=chord_annotations,
                  interval_figures=interval_figures,
                  use_clefs=use_clefs)


def notes_to_midi(notes):
    # r is rest
    # takes in list of list
    # # is sharp
    # b is flat
    # letters should be all caps!
    # C4 = C in 4th octave
    # 0 = rest
    # 12 = C0
    # 24 = C1
    # 36 = C2
    # 48 = C3
    # 60 = C4
    # 72 = C5
    # 84 = C6
    base = {"C": 0,
            "D": 2,
            "E": 4,
            "F": 5,
            "G": 7,
            "A": 9,
            "B": 11}
    pitch_list = []
    for nl in notes:
        pitch_line = []
        for nn in nl:
            if nn == "R":
                base_pitch = 0
                offset = 0
                octave = 0
            elif "#" in nn:
                base_pitch = base[nn[0]]
                offset = 1
                octave = (int(nn[-1]) + 1) * 12
            elif "b" in nn:
                base_pitch = base[nn[0]]
                offset = -1
                octave = (int(nn[-1]) + 1) * 12
            else:
                base_pitch = base[nn[0]]
                offset = 0
                octave = (int(nn[-1]) + 1) * 12
            r = base_pitch + octave + offset
            pitch_line.append(r)
        pitch_list.append(pitch_line)
    return pitch_list


def normalize_parts_with_durations(parts, durations):
    value_durations = [[durations_map[dd] for dd in d] for d in durations]
    cumulative_durations = [np.cumsum(vd) for vd in value_durations]
    for n in range(len(parts)):
        cumulative_durations[n] = np.concatenate(([0.], cumulative_durations[n]))

    # everything is the same at the start
    normed_parts = []
    normed_durations = []
    for n in range(len(parts)):
        normed_parts.append([])
        normed_durations.append([])
    step_i = [0 for p in parts]
    held_p_i = [-1 for p in parts]
    finished = False
    # should divide into .5, .33, .25, .125, .0625 (no support smaller than 64th notes...)
    check_min = min([vd for d in value_durations for vd in d])
    cumulative_max = max([cd for d in cumulative_durations for cd in d])

    assert check_min >= .0625
    time_inc = .005
    time = 0.
    prev_event_time = 0.

    n_comb = 3
    exact_timings = [0., 0.0625, 0.125, .25, 0.5, 1., 2., 4.]
    all_exact_timings = list(itertools.product(exact_timings[3:], repeat=n_comb))
    exact_timings = exact_timings[:3] + [sum(et) for et in all_exact_timings]

    while not finished:
        # move in small increments, but only append when an event triggers
        # in any channel
        # check if an event happened
        is_event = False
        which_events = []
        for n in range(len(parts)):
            if time < cumulative_durations[n][step_i[n]]:
                pass
            else:
                is_event = True
                which_events.append(n)

        if is_event:
            for n in range(len(parts)):
                tt = round(time - prev_event_time, 4)
                min_i = np.argmin([np.abs(et - tt) for et in exact_timings])
                tt = exact_timings[min_i]
                if n in which_events:
                    normed_parts[n].append(parts[n][step_i[n]])
                    normed_durations[n].append(tt)
                    held_p_i[n] = parts[n][step_i[n]]
                    step_i[n] += 1
                else:
                    normed_parts[n].append(held_p_i[n])
                    normed_durations[n].append(tt)
            prev_event_time = time
        time += time_inc
        if time >= cumulative_max:
            for n in range(len(parts)):
                # backfill the final timestep...
                tt = round(cumulative_durations[n][-1] - prev_event_time, 4)
                min_i = np.argmin([np.abs(et - tt) for et in exact_timings])
                tt = exact_timings[min_i]
                normed_durations[n].append(tt)
            finished = True
    normed_durations = [nd[1:] for nd in normed_durations]
    normed_durations = [[inverse_durations_map[fracf(ndi)] for ndi in nd] for nd in normed_durations]
    assert len(normed_parts) == len(normed_durations)
    assert all([len(n_p) == len(n_d) for n_p, n_d in zip(normed_parts, normed_durations)])
    return normed_parts, normed_durations


def fixup_parts_durations(parts, durations):
    if len(parts[0]) != len(parts[1]):
        new_parts, new_durations = normalize_parts_with_durations(parts, durations)
        parts = new_parts
        durations = new_durations
    return parts, durations


def intervals_from_midi(parts, durations):
    if len(parts) < 2:
        raise ValueError("Must be at least 2 parts to compare intervals")
    if len(parts) > 2:
        raise ValueError("NYI")

    intervals = []
    this_intervals = []

    parts, durations = fixup_parts_durations(parts, durations)

    assert len(parts) == len(durations)
    for p, d in zip(parts, durations):
        assert len(p) == len(d)

    proposed = np.array(parts[0]) - np.array(parts[1])
    for idx, p in enumerate(proposed):
        try:
            this_intervals.append(intervals_map[p])
        except:
            assert len(parts) == 2
            if parts[0][idx] == 0:
                # rest in part 0
                #print("Possible rest in part0")
                this_intervals.append("R" + intervals_map[0])

            if parts[1][idx] == 0:
                # rest in part 1
                #print("Possible rest in part1")
                this_intervals.append("R" + intervals_map[0])
        """
        # strip off name
        if full_name:
            this_intervals.append(intervals_map[p])
        else:
            nm = intervals_map[p]
            if "-" not in nm:
                this_intervals.append(nm[1:])
            else:
                this_intervals.append(nm[2:])
        """
    intervals.append(this_intervals)
    return intervals


def motion_from_midi(parts, durations):
    if len(parts) != 2:
        raise ValueError("NYI")

    parts, durations = fixup_parts_durations(parts, durations)

    # similar, oblique, contrary, direct
    p0 = np.array(parts[0])
    p1 = np.array(parts[1])
    dp0 = p0[1:] - p0[:-1]
    dp1 = p1[1:] - p1[:-1]
    # first motion is always start...
    motions = ["START"]
    for dip0, dip1 in zip(dp0, dp1):
        if dip0 == 0 or dip1 == 0:
            motions.append("OBLIQUE")
        elif dip0 == dip1:
            motions.append("DIRECT")
        elif dip0 > 0 and dip1 < 0:
            motions.append("CONTRARY")
        elif dip0 < 0 and dip1 > 0:
            motions.append("CONTRARY")
        elif dip0 < 0 and dip1 < 0:
            motions.append("SIMILAR")
        elif dip0 > 0 and dip1 > 0:
            motions.append("SIMILAR")
        else:
            raise ValueError("Should never see this case!")
    motions.append("END")
    return [motions]


def rules_from_midi(parts, durations, key_signature):
    parts, durations = fixup_parts_durations(parts, durations)
    full_intervals = intervals_from_midi(parts, durations)
    full_motions = motion_from_midi(parts, durations)

    assert len(full_intervals) == len(full_motions)
    all_rulesets = []
    i = 0
    for fi, fm in zip(full_intervals, full_motions):
        fimi = 0
        this_ruleset = []
        while i < len(fi):
            this_interval = fi[i]
            this_motion = fm[i]
            this_notes = tuple([p[i] for p in parts])
            last_interval = None
            last_motion = None
            last_notes = None
            if i > 0:
                last_interval = fi[i - 1]
                last_notes = tuple([p[i - 1] for p in parts])
                last_motion = fm[i - 1]
            this_ruleset.append(make_rule(this_interval, this_motion, this_notes,
                                          key_signature,
                                          last_interval, last_motion, last_notes))
            i += 1
        all_rulesets.append(this_ruleset)
    assert len(all_rulesets[0]) == len(full_intervals[0])
    for ar in all_rulesets:
        assert len(ar) == len(all_rulesets[0])
    return all_rulesets

# previous movement, previous interval, previous notes
rule_template = "{}:{}:{},{}->{}:{}:{},{}"
# key, top note, bottom note
reduced_template = "K{},{},{}->{}:{}:{},{}"

# todo, figure out others...
base_pitch_map = {"C": 0,
                  "C#": 1,
                  "D": 2,
                  "Eb": 3,
                  "E": 4,
                  "F": 5,
                  "F#": 6,
                  "G": 7,
                  "G#": 8,
                  "A": 9,
                  "Bb": 10,
                  "B": 11}
base_note_map = {v: k for k, v in base_pitch_map.items()}

key_signature_map = {}
key_signature_map["C"] = 0
key_signature_inv_map = {v: k for k, v in key_signature_map.items()}

time_signature_map = {}
time_signature_map["4/4"] = (4, 1)

key_check = {"C": ["C", "D", "E", "F", "G", "A", "B"]}
intervals_map = {-16: "-M10",
                -15: "-m10",
                -14: "-M9",
                -13: "-m9",
                -12: "-P8",
                -11: "-m2",
                -10: "-M2",
                -9: "-m3",
                -8: "-M3",
                -7: "-P4",
                -6: "-a4",
                -5: "-P5",
                -4: "-m6",
                -3: "-M6",
                -2: "-m7",
                -1: "-M7",
                0: "P1",
                1: "m2",
                2: "M2",
                3: "m3",
                4: "M3",
                5: "P4",
                6: "a4",
                7: "P5",
                8: "m6",
                9: "M6",
                10: "m7",
                11: "M7",
                12: "P8",
                13: "m9",
                14: "M9",
                15: "m10",
                16: "M10",
                17: "P11",
                18: "a11",
                19: "P12",
                20: "m13",
                21: "M13"}

inverse_intervals_map = {v: k for k, v in intervals_map.items()}

def fracf(f):
    return fractions.Fraction(f)

inverse_durations_map = {fracf(8.): "\\breve",
                         fracf(6.): ".4",
                         fracf(4.): "4",
                         fracf(3.): ".2",
                         fracf(2.): "2",
                         fracf(1.5): ".1",
                         fracf(1.): "1",
                         fracf(.75): ".8th",
                         fracf(.5): "8th",
                         fracf(.25): "16th",
                         fracf(.125): "32nd",
                         fracf(.0625): "64th"}

durations_map = {v: k for k, v in inverse_durations_map.items()}

perfect_intervals = {"P1": None,
                     "P8": None,
                     "P5": None,
                     "P4": None}
neg_perfect_intervals = {"-P8": None,
                         "-P5": None,
                         "-P4": None}
harmonic_intervals = {"RP1": None,
                      "P1": None,
                      "P8": None,
                      "P5": None,
                      "P4": None,
                      "m3": None,
                      "M3": None,
                      "m6": None,
                      "M6": None,
                      "m10": None,
                      "M10": None,
                      "m13": None,
                      "M13": None}
neg_harmonic_intervals = {"-P8": None,
                          "-P5": None,
                          "-P4": None,
                          "-m3": None,
                          "-M3": None,
                          "-m6": None,
                          "-M6": None}

nonharmonic_intervals = {"m2": None,
                         "M2": None,
                         "a4": None,
                         "m7": None,
                         "M7": None,
                         "m9": None,
                         "M9": None,
                         "a11": None}
neg_nonharmonic_intervals = {"-m2": None,
                             "-M2": None,
                             "-a4": None,
                             "-m7": None,
                             "-M7": None,
                             "-m9": None,
                             "-M9": None,
                             "-a11": None}

hamonic_intervals = {k: v for k, v in inverse_intervals_map.items()
                     if k in harmonic_intervals}

allowed_perfect_motion = {"CONTRARY": None,
                          "OBLIQUE": None}

def midi_to_notes(parts):
    all_parts = []
    for p in parts:
        this_notes = []
        for pi in p:
            if pi == 0:
                this_notes.append("R")
                continue
            octave = pi // 12 - 1
            pos = base_note_map[pi % 12]
            this_notes.append(pos + str(octave))
        all_parts.append(this_notes)
    return all_parts


def make_rule(this_interval, this_motion, this_notes, key_signature,
              last_interval=None, last_motion=None, last_notes=None):
    if last_interval is not None:
        str_last_notes = midi_to_notes([last_notes])[0]
        str_this_notes = midi_to_notes([this_notes])[0]
        nt = rule_template.format(last_motion, last_interval,
                                  str_last_notes[0], str_last_notes[1],
                                  this_motion, this_interval,
                                  str_this_notes[0], str_this_notes[1])
    else:
        key = key_signature_inv_map[key_signature]
        str_notes = midi_to_notes([this_notes])[0]
        nt = reduced_template.format(key, str_notes[0], str_notes[1], this_motion, this_interval, str_notes[0], str_notes[1])
    return nt


def estimate_mode(parts, durations, rules, key_signature):
    parts, durations = fixup_parts_durations(parts, durations)
    first_note = [p[0] for p in parts]
    final_notes = [p[-2:] for p in parts]
    final_notes = np.array(final_notes)
    first_note = np.array(first_note)
    dfinal_notes = final_notes[-1, -1] - final_notes[-1, 0]
    if dfinal_notes == 1.:
        # final cadence indicates the tonic
        # bass almost always ends on I, i, etc except in half cadence...
        mode = midi_to_notes([[final_notes[-1, -1]]])[0][0][:-1] # strip octave
        return mode
    elif final_notes[-1, -1] == final_notes[0, 0]:
        mode = midi_to_notes([[final_notes[-1, -1]]])[0][0][:-1] # strip octave
        return mode
    elif rules[-1][-1].split("->")[-1].split(":")[1] in ["P8", "P1"]:
        mode = midi_to_notes([[final_notes[-1, -1]]])[0][0][:-1] # strip octave
        return mode
    else:
        print("Unknown mode estimate...")
        from IPython import embed; embed(); raise ValueError()
    raise ValueError("This function must return before the end! Bug, rule {}".format(rule))


def rsp(rule):
    return rule.split("->")


def key_start_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    # ignore voices not used
    rules = rules_from_midi(parts, durations, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    for rule in rules:
        last, this = rsp(rule)
        if "K" in last:
            tm, ti, tn = this.split(":")
            lk, lns, lnb = last.split(",")
            # get rid of the K in the front
            lk = lk[1:]
            # check that note is in key?
            if ti == "P8" or ti == "P5" or ti == "P1" or ti == "RP1":
                if lnb[:-1] == mode or lnb == "R":
                    returns.append((True, "key_start_rule: TRUE, start is in mode"))
                else:
                    returns.append((False, "key_start_rule: FALSE, first bass note {} doesn't match estimated mode {}".format(lnb, mode)))
            else:
                returns.append((False, "key_start_rule: FALSE, first interval {} is not in ['P1', 'P5', 'P8']".format(ti)))
        else:
            returns.append((None, "key_start_rule: NONE, not applicable"))
    return returns


def next_step_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    rules = rules_from_midi(parts, durations, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    for rule in rules:
        last, this = rsp(rule)
        tm, ti, tn = this.split(":")
        tn0, tn1 = tn.split(",")
        try:
            lm, li, ln = last.split(":")
        except ValueError:
            returns.append((None, "next_step_rule: NONE, not applicable"))
            continue
        ln0, ln1 = ln.split(",")
        dn0 = np.diff(np.array(notes_to_midi([[tn0, ln0]])[0]))
        dn1 = np.diff(np.array(notes_to_midi([[tn1, ln1]])[0]))
        note_sets = [[ln0, tn0], [ln1, tn1]]
        voice_ok = None
        msg = None
        for n, voice_step in enumerate([dn0, dn1]):
            try:
                this_step = intervals_map[-int(voice_step)]
            except KeyError:
                if note_sets[n][0] == "R":
                    if msg is None:
                        msg = "next_step_rule: NONE, rest in voice"
                    continue
            if ignore_voices is not None and n in ignore_voices:
                if msg is None:
                    msg = "next_step_rule: NONE, skipped voice"
                continue
            if voice_ok is False:
                continue
            if this_step in ["a4", "-a4"]:
                msg = "next_step_rule: FALSE, voice {} stepwise movement {}->{}, {} not allowed".format(n, note_sets[n][0], note_sets[n][1], this_step)
                voice_ok = False
            elif this_step in ["P8", "-P8", "m6", "M6", "-m6", "-M6", "-M3", "-m3"]:
                msg = "next_step_rule: TRUE, voice {} skip {}->{}, {} acceptable".format(n, note_sets[n][0], note_sets[n][1], this_step)
                voice_ok = True
            elif abs(int(voice_step)) > 7:
                msg = "next_step_rule: FALSE, voice {} stepwise skip {}->{}, {} too large".format(n, note_sets[n][0], note_sets[n][1], this_step)
                voice_ok = False
            else:
                msg = "next_step_rule: TRUE, step move valid"
                voice_ok = True
        returns.append((voice_ok, msg))
    return returns


def leap_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    rules = rules_from_midi(parts, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    returns.extend([(None, "leap_rule: NONE, not applicable")] * 2)
    for i in range(2, len(parts[0])):
        msg = None
        voice_ok = None
        for n in range(len(parts)):
            if ignore_voices is not None and n in ignore_voices:
                if msg is None:
                    msg = "leap_rule: NONE, skipped voice"
                continue
            prev_jmp = parts[n][i - 1] - parts[n][i - 2]
            cur_step = parts[n][i] - parts[n][i - 1]
            if abs(prev_jmp) > 3:
                is_opposite = math.copysign(1, cur_step) != math.copysign(1, prev_jmp)
                is_step = abs(cur_step) == 1 or abs(cur_step) == 2
                # check if it outlines a triad?
                if is_opposite and is_step:
                    msg = "leap_rule: TRUE, voice {} leap of {} corrected".format(n, prev_jmp)
                    voice_ok = True
                else:
                    msg = "leap_rule: FALSE, voice {} leap of {} not corrected".format(n, prev_jmp)
                    voice_ok = False
            else:
                msg = "leap_rule: NONE, not applicable"
                voice_ok = None
        returns.append((voice_ok, msg))
    assert len(returns) == len(parts[0])
    return returns


def parallel_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    # ignore voices not used
    rules = rules_from_midi(parts, durations, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    for idx, rule in enumerate(rules):
        last, this = rsp(rule)
        tm, ti, tn = this.split(":")
        tn0, tn1 = tn.split(",")
        try:
            lm, li, ln = last.split(":")
        except ValueError:
            returns.append((None, "parallel_rule: NONE, not applicable"))
            continue
        ln0, ln1 = ln.split(",")
        dn0 = np.diff(np.array(notes_to_midi([[tn0, ln0]])[0]))
        dn1 = np.diff(np.array(notes_to_midi([[tn1, ln1]])[0]))
        note_sets = [[ln0, tn0], [ln1, tn1]]
        if li == "M10" or li == "m10":
            if ti == "P8" and timings[0][idx] == 0.:
                # battuta octave
                returns.append((False, "parallel_rule: FALSE, battuta octave {}->{} disallowed on first beat".format(li, ti)))
                continue
        if ti in perfect_intervals or ti in neg_perfect_intervals:
            if tm in allowed_perfect_motion:
                returns.append((True, "parallel_rule: TRUE, movement {} into perfect interval {} allowed".format(tm, ti)))
                continue
            else:
                returns.append((False, "parallel_rule: FALSE, movement {} into perfect interval {} not allowed".format(tm, ti)))
                continue
        elif ti in harmonic_intervals or ti in neg_harmonic_intervals or ti in nonharmonic_intervals or ti in neg_nonharmonic_intervals:
            # allowed note check is elsewhere
            returns.append((True, "parallel_rule: TRUE, all movements including {} allowed into interval {}".format(tm, ti)))
        else:
            print("parallel_rule: shouldn't get here")
            from IPython import embed; embed(); raise ValueError()
            raise ValueError("parallel_rule: shouldn't get here")
    return returns


def beat_parallel_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    # ignore voices not used
    rules = rules_from_midi(parts, durations, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    for idx, rule in enumerate(rules):
        last, this = rsp(rule)
        tm, ti, tn = this.split(":")
        tn0, tn1 = tn.split(",")
        try:
            lm, li, ln = last.split(":")
        except ValueError:
            returns.append((None, "beat_parallel_rule: NONE, not applicable"))
            continue
        ln0, ln1 = ln.split(",")

        dn0 = np.diff(np.array(notes_to_midi([[tn0, ln0]])[0]))
        dn1 = np.diff(np.array(notes_to_midi([[tn1, ln1]])[0]))
        note_sets = [[ln0, tn0], [ln1, tn1]]

        # rP1 is rest
        if ti in ["P8", "P5"]:
            if idx < 2:
                returns.append((True, "beat_parallel_rule: TRUE, no earlier parallel move"))
                continue
            plast, pthis = rsp(rules[idx - 2])
            pm, pi, pn = pthis.split(":")
            if pi in ["P8", "P5"] and pi == ti:
                # check beats - use the 0th voice?
                if 0. == timings[0][idx] and 0. == timings[0][idx - 2] and abs(inverse_intervals_map[li]) < 5:
                    returns.append((False, "beat_parallel_rule: FALSE, previous downbeat had parallel perfect interval {}".format(pi)))
                    continue
            returns.append((True, "beat_parallel_rule: TRUE, no beat parallel move"))
        else:
            returns.append((True, "beat_parallel_rule: TRUE, no beat parallel move"))
    return returns


def bar_consonance_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    # ignore voices not used
    rules = rules_from_midi(parts, durations, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    assert all([len(timings[i]) == len(timings[0]) for i in range(len(timings))])
    for idx, rule in enumerate(rules):
        last, this = rsp(rule)
        tm, ti, tn = this.split(":")
        tn0, tn1 = tn.split(",")

        timing_i = timings[0][idx]
        for n in range(len(timings)):
            assert timings[n][idx] == timing_i

        if timing_i == 0.:
            if ti in harmonic_intervals or ti in neg_harmonic_intervals:
                returns.append((True, "bar_consonance_rule: TRUE, harmonic interval {} allowed on downbeat".format(ti)))
            else:
                returns.append((False, "bar_consonance_rule: FALSE, non-consonant interval {} disallowed on downbeat".format(ti)))
        elif timing_i != 0.:
            returns.append((None, "bar_consonance_rule: NONE, rule not applicable on beat {}".format(timing_i)))
        else:
            raise ValueError("bar_consonance_rule: shouldn't get here")
    return returns


def passing_tone_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    # ignore voices not used
    rules = rules_from_midi(parts, durations, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    assert all([len(timings[i]) == len(timings[0]) for i in range(len(timings))])
    for idx, rule in enumerate(rules):
        last, this = rsp(rule)
        tm, ti, tn = this.split(":")
        tn0, tn1 = tn.split(",")

        timing_i = timings[0][idx]
        for n in range(len(timings)):
            assert timings[n][idx] == timing_i

        if timing_i == 0.:
            returns.append((None, "passing_tone_rule: NONE, rule not applicable on beat {}".format(timing_i)))
        elif timing_i != 0.:
            if ti in harmonic_intervals or ti in neg_harmonic_intervals:
                returns.append((True, "passing_tone_rule: TRUE, harmonic interval {} allowed on downbeat".format(ti)))
            else:
                lm, li, ln = last.split(":")
                ln0, ln1 = ln.split(",")
                # passing tone check
                pitches = np.array(notes_to_midi([[ln0, ln1], [tn0, tn1]]))
                last_diffs = np.diff(pitches, axis=0)

                this, nxt = rsp(rules[idx + 1])
                nm, ni, nn = nxt.split(":")
                nn0, nn1 = nn.split(",")
                pitches = np.array(notes_to_midi([[tn0, tn1], [nn0, nn1]]))
                nxt_diffs = np.diff(pitches, axis=0)

                not_skip = [n for n in range(last_diffs.shape[1]) if n not in ignore_voices]
                last_diffs = last_diffs[:, not_skip]
                nxt_diffs = nxt_diffs[:, not_skip]
                last_ok = np.where(np.abs(last_diffs) >= 3)[0]
                nxt_ok = np.where(np.abs(nxt_diffs) >= 3)[0]
                if len(last_ok) == 0 and len(nxt_ok) == 0:
                    returns.append((True, "passing_tone_rule: TRUE, passing tones allowed on upbeat"))
                else:
                    returns.append((False, "passing_tone_rule: FALSE, non-passing tones not allowed on upbeat"))
        else:
            raise ValueError("passing_tone_rule: shouldn't get here")
    return returns


def sequence_step_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    rules = rules_from_midi(parts, durations, key_signature)
    rules = rules[0]
    key = key_signature_inv_map[key_signature]
    returns = []
    assert all([len(timings[i]) == len(timings[0]) for i in range(len(timings))])
    last_timing_i = 0.
    for idx, rule in enumerate(rules):
        last, this = rsp(rule)
        tm, ti, tn = this.split(":")
        tn0, tn1 = tn.split(",")

        timing_i = timings[0][idx]
        for n in range(len(timings)):
            assert timings[n][idx] == timing_i

        time_num = time_signature[0]
        time_denom = time_signature[1]

        diff_timing_i = timing_i - last_timing_i
        # diff timing is circular
        if timing_i == 0. and last_timing_i == 3.:
            diff_timing_i = 1.
        last_timing_i = timing_i
        # force to match quarters
        if timing_i not in [0., 1., 2., 3.]:
            raise ValueError("sequence_step_rule: timing not recognized!")
        if idx < 1 or abs(diff_timing_i) != 1.:
            returns.append((None, "sequence_step_rule: NONE, not applicable at step {}".format(idx)))
            continue
        elif abs(diff_timing_i) == 1.:
            lm, li, ln = last.split(":")
            ln0, ln1 = ln.split(",")

            pitches = np.array(notes_to_midi([[ln0, ln1], [tn0, tn1]]))
            last_diffs = np.diff(pitches, axis=0)
            not_skip = [n for n in range(last_diffs.shape[1]) if n not in ignore_voices]
            last_diffs = last_diffs[:, not_skip]
            last_ok = np.where(np.abs(last_diffs) >= 3)[0]

            if idx + 1 == len(rules):
                if ti in harmonic_intervals or ti in neg_harmonic_intervals:
                    returns.append((True, "sequence_step_rule: TRUE, interval {} always allowed".format(ti)))
                elif len(last_ok) == 0 and timing_i not in [0., 2.]:
                    returns.append((True, "sequence_step_rule: TRUE, interval {} is a continuation".format(ti)))
                else:
                    returns.append((False, "sequence_step_rule: FALSE, interval {} disallowed in termination".format(ti)))
                continue

            this, nxt = rsp(rules[idx + 1])
            nm, ni, nn = nxt.split(":")
            nn0, nn1 = nn.split(",")
            pitches = np.array(notes_to_midi([[tn0, tn1], [nn0, nn1]]))
            nxt_diffs = np.diff(pitches, axis=0)
            nxt_diffs = nxt_diffs[:, not_skip]
            nxt_ok = np.where(np.abs(nxt_diffs) >= 3)[0]

            if ti in harmonic_intervals or ti in neg_harmonic_intervals:
                returns.append((True, "sequence_step_rule: TRUE, interval {} always allowed".format(ti)))
            else:
                if timing_i == 0.:
                    returns.append((False, "sequence_step_rule: FALSE, cannot have non-harmonic interval {} on bar part 0.".format(ti)))
                elif timing_i == 1.:
                    if len(nxt_ok) == 0 and len(last_ok) == 0:
                        if ni in harmonic_intervals or ni in neg_harmonic_intervals:
                            returns.append((True, "sequence_step_rule: TRUE, interval {} at bar part 1. allowed as part of continuation".format(ti)))
                        else:
                            returns.append((False, "sequence_step_rule: FALSE, interval {} at bar part 1. not allowed, next interval not harmonic".format(ti)))
                    else:
                        nxt, nxtnxt = rsp(rules[idx + 2])
                        nnm, nni, nnn = nxtnxt.split(":")
                        nnn0, nnn1 = nnn.split(",")
                        pitches = np.array(notes_to_midi([[nn0, nn1], [nnn0, nnn1]]))
                        nxtnxt_diffs = np.diff(pitches, axis=0)
                        nxtnxt_diffs = nxtnxt_diffs[:, not_skip]
                        nxtnxt_ok = np.where(np.abs(nxtnxt_diffs) >= 3)[0]
                        nxtnxt_resolves = np.where(np.sign(nxtnxt_diffs) != np.sign(nxt_diffs))[0]

                        # check that it resolves in cambiata...
                        if len(nxt_ok) == 1 and len(nxtnxt_ok) == 0 and nni in harmonic_intervals and sum(nxtnxt_resolves) == 0:
                            if not_skip == [1]:
                                info_tup = (tn1, nn1, nnn1)
                            elif not_skip == [0]:
                                info_tup = (tn0, nn0, nnn0)
                            else:
                                print("sequence_step_rule: other not_skip voices not yet supported...")
                                from IPython import embed; embed(); raise ValueError()

                            returns.append((True, "sequence_step_rule: TRUE, cambiata {}->{}->{} in voice {} detected at bar part 1. to 3.".format(info_tup[0], info_tup[1], info_tup[2], not_skip[0])))
                        else:
                            returns.append((False, "sequence_step_rule: FALSE, interval {} at bar part 1. not allowed, not a continuation or cambiata".format(ti)))
                elif timing_i == 2.:
                    # last and next must be harmonic, and must be continuation...
                    if len(nxt_ok) == 0 and len(last_ok) == 0:
                        if ni in harmonic_intervals or ni in neg_harmonic_intervals:
                            returns.append((True, "sequence_step_rule: TRUE, interval {} at bar part 2. allowed as part of continuation".format(ti)))
                        else:
                            returns.append((False, "sequence_step_rule: FALSE, interval {} at bar part 2. not allowed, next interval not harmonic or no continuation".format(ti)))
                elif timing_i == 3.:
                    if len(nxt_ok) == 0 and len(last_ok) == 0:
                        if ni in harmonic_intervals or ni in neg_harmonic_intervals:
                            returns.append((True, "sequence_step_rule: TRUE, interval {} at bar part 3. allowed as part of continuation".format(ti)))
                        else:
                            returns.append((False, "sequence_step_rule: FALSE, interval {} at bar part 3. not allowed, next interval not harmonic".format(ti)))
                    else:
                        returns.append((False, "sequence_step_rule: FALSE, interval {} at bar part 3. not allowed, not a continuation".format(ti)))
                else:
                    print("sequence_step_rule: shouldn't get here")
                    from IPython import embed; embed(); raise ValueError()
        else:
            print("sequence_step_rule, shouldn't get here")
            from IPython import embed; embed(); raise ValueError()
    return returns

species1_rules_map = OrderedDict()
species1_rules_map["key_start_rule"] = key_start_rule
species1_rules_map["bar_consonance_rule"] = bar_consonance_rule
species1_rules_map["next_step_rule"] = next_step_rule
species1_rules_map["parallel_rule"] = parallel_rule

# leap rule is not a rule :|
#all_rules_map["leap_rule"] = leap_rule

def check_species1_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    res = [species1_rules_map[arm](parts, durations, key_signature, time_signature, mode, timings, ignore_voices) for arm in species1_rules_map.keys()]

    global_check = True
    for r in res:
        rr = [True if ri[0] is True or ri[0] is None else False for ri in r]
        if all(rr):
            pass
        else:
            global_check = False
    return (global_check, res)

species2_rules_map = OrderedDict()
species2_rules_map["key_start_rule"] = key_start_rule
species2_rules_map["bar_consonance_rule"] = bar_consonance_rule
species2_rules_map["parallel_rule"] = parallel_rule
species2_rules_map["beat_parallel_rule"] = beat_parallel_rule
species2_rules_map["next_step_rule"] = next_step_rule
species2_rules_map["passing_tone_rule"] = passing_tone_rule
def check_species2_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    res = [species2_rules_map[arm](parts, durations, key_signature, time_signature, mode, timings, ignore_voices) for arm in species2_rules_map.keys()]

    global_check = True
    for r in res:
        rr = [True if ri[0] is True or ri[0] is None else False for ri in r]
        if all(rr):
            pass
        else:
            global_check = False
    return (global_check, res)

species3_rules_map = OrderedDict()
species3_rules_map["key_start_rule"] = key_start_rule
species3_rules_map["bar_consonance_rule"] = bar_consonance_rule
species3_rules_map["parallel_rule"] = parallel_rule
species3_rules_map["beat_parallel_rule"] = beat_parallel_rule
species3_rules_map["next_step_rule"] = next_step_rule
species3_rules_map["sequence_step_rule"] = sequence_step_rule
def check_species3_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices):
    res = [species3_rules_map[arm](parts, durations, key_signature, time_signature, mode, timings, ignore_voices) for arm in species3_rules_map.keys()]

    global_check = True
    for r in res:
        rr = [True if ri[0] is True or ri[0] is None else False for ri in r]
        if all(rr):
            pass
        else:
            global_check = False
    return (global_check, res)



def make_timings(durations, beats_per_measure, duration_unit):
    # use normalized_durations?
    if beats_per_measure != 4:
        raise ValueError("beats per measure {} needs support in handle_durations".format(beats_per_measure))

    if duration_unit != 1:
        raise ValueError("duration unit {} needs support in handle_durations".format(duration_unit))

    # U for upbeat, D for downbeat?
    all_lines = []
    all_timings = []

    if beats_per_measure == 4 and duration_unit == 1:
        pass
    else:
        raise ValueError("Beats per measure {} and duration unit {} NYI".format(beats_per_measure, duration_unit))

    value_durations = [[float(durations_map[di]) for di in d] for d in durations]
    cumulative_starts = [np.concatenate(([0.], np.cumsum(vd)))[:-1] for vd in value_durations]
    for cline in cumulative_starts:
        this_lines = []
        for cl in cline:
            this_lines.append(cl % beats_per_measure)
            #if cl % beats_per_measure in downbeats:
            #    this_lines.append("D")
            #else:
            #    this_lines.append("U")
        all_lines.append(this_lines)
    return all_lines


def estimate_timing(parts, durations, time_signature):
    # returns U or D for each part if it starts on upbeat or downbeat
    parts, durations = fixup_parts_durations(parts, durations)
    beats_per_measure = time_signature[0]
    duration_unit = time_signature[1]
    ud = make_timings(durations, beats_per_measure, duration_unit)
    return ud


def analyze_2voices(parts, durations, key_signature_str, time_signature_str, species="species1",
                    cantus_firmus_voices=None):
    # not ideal but keeps stuff consistent
    key_signature = key_signature_map[key_signature_str]
    # just check that it parses here
    time_signature = time_signature_map[time_signature_str]
    beats_per_measure = time_signature[0]
    duration_unit = time_signature[1]

    parts, durations = fixup_parts_durations(parts, durations)

    rules = rules_from_midi(parts, durations, key_signature)
    mode = estimate_mode(parts, durations, rules, key_signature)
    timings = estimate_timing(parts, durations, time_signature)

    ignore_voices = cantus_firmus_voices
    if species == "species1":
        r = check_species1_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices)
    elif species == "species2":
        r = check_species2_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices)
    elif species == "species3":
        r = check_species3_rule(parts, durations, key_signature, time_signature, mode, timings, ignore_voices)
    else:
        raise ValueError("Unknown species argument {}".format(species))
    all_ok = r[0]
    this_ok = []
    true_false = OrderedDict()
    true_false["True"] = []
    true_false["False"] = []
    for rr in r[1]:
        for n in range(len(rr)):
            this_ok.append((n, rr[n][0], rr[n][1]))
            if rr[n][0] == True or rr[n][0] == None:
                true_false["True"].append(n)
            else:
                true_false["False"].append(n)
    true_false["True"] = sorted(list(set(true_false["True"])))
    true_false["False"] = sorted(list(set(true_false["False"])))
    return (all_ok, true_false, rules, sorted(this_ok))


def test_species1():
    print("Running test for species1...")
    all_ex = []

    # All figure numbers from Gradus ad Parnassum
    # fig 5, correct notes
    ex = {"notes": [["A3", "A3", "G3", "A3", "B3", "C4", "C4", "B3", "D4", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["4"] * 11, ["4"] * 11],
          "answers": [True] * 11,
          "name": "fig5",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 6, initial (incorrect) notes
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["G2", "D3", "A2", "F2", "E2", "D2", "F2", "C3", "D3", "C#3", "D3"]],
          "durations": [["4"] * 11, ["4"] * 11],
          "answers": [True if n not in [0, 2] else False for n in range(11)],
          "name": "fig6w",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 6, correct notes
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["D2", "D2", "A2", "F2", "E2", "D2", "F2", "C3", "D3", "C#3", "D3"]],
          "durations": [["4"] * 11, ["4"] * 11],
          "answers": [True] * 11,
          "name": "fig6c",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 11, correct notes
    ex = {"notes": [["B3", "C4", "F3", "G3", "A3", "C4", "B3", "E4", "D4", "E4"],
                    ["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"]],
          "durations": [["4"] * 10, ["4"] * 10],
          "answers": [True] * 10,
          "name": "fig11",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 12, incorrect notes
    ex = {"notes": [["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"],
                    ["E2", "A2", "D2", "E2", "F2", "F2", "B2", "C3", "D3", "E3"]],
          "durations": [["4"] * 10, ["4"] * 10],
          "answers": [True if n not in [6,] else False for n in range(10)],
          "name": "fig12w",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 13, correct notes
    ex = {"notes": [["F3", "E3", "C3", "F3", "F3", "G3", "A3", "G3", "C3", "F3", "E3", "F3"],
                    ["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig13",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 14, correct notes w/ voice crossing
    ex = {"notes": [["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"],
                    ["F2", "E2", "F2", "A2", "Bb2", "G2", "A2", "E2", "F2", "D2", "E2", "F2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig14",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 15, incorrect notes
    ex = {"notes": [["G3", "E3", "D3", "G3", "G3", "G3", "A3", "B3", "G3", "E4", "D4", "G3", "F#3", "G3"],
                    ["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"]],
          "durations": [["4"] * 14, ["4"] * 14],
          "answers": [True if n not in [10,] else False for n in range(14)],
          "name": "fig15w",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 15, correct notes
    ex = {"notes": [["G3", "E3", "D3", "G3", "G3", "G3", "A3", "B3", "G3", "C4", "A3", "G3", "F#3", "G3"],
                    ["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"]],
          "durations": [["4"] * 14, ["4"] * 14],
          "answers": [True] * 14,
          "name": "fig15c",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 21, correct notes
    ex = {"notes": [["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"],
                    ["G2", "A2", "G2", "E2", "E2", "C2", "G2", "B2", "C3", "A2", "F#2", "G2", "F#2", "G2"]],
          "durations": [["4"] * 14, ["4"] * 14],
          "answers": [True] * 14,
          "name": "fig21",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 22, correct notes
    ex = {"notes": [["A3", "E3", "G3", "F3", "E3", "C4", "A3", "B3", "B3", "A3", "G#3", "A3"],
                    ["A2", "C3", "B2", "D3", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig22",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 23, correct notes
    ex = {"notes": [["A2", "C3", "B2", "D3", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"],
                    ["A2", "A2", "G2", "F2", "E2", "E2", "D2", "C2", "G2", "A2", "G#2", "A2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig23",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    for ex in all_ex:
        notes = ex["notes"]
        durations = ex["durations"]
        answers = ex["answers"]
        fig_name = ex["name"]
        ig = [ex["cantus_firmus_voice"],]
        parts = notes_to_midi(notes)
        # TODO: handle strings like "C"
        key_signature = "C"
        # as in sheet music
        time_signature = "4/4"
        # durations can be "64th", "32nd", "16th", "8th", "1", "2", "4", "8"
        # also any of these can be dotted (".") e.g. ".8th" (dotted eighth)
        # or summed for a tie "1+8th"
        # TODO: Triplets?
        aok = analyze_2voices(parts, durations, key_signature, time_signature,
                              species="species1", cantus_firmus_voices=ig)
        aok_lu = aok[1]
        aok_rules = aok[2]

        all_answers = [-1] * len(answers)
        for a in aok[-1]:
            if all_answers[a[0]] == -1:
                all_answers[a[0]] = a[1]
            else:
                if a[1] in [None, True]:
                    if all_answers[a[0]] == None:
                        all_answers[a[0]] = True
                    else:
                        all_answers[a[0]] &= True
                else:
                    if all_answers[a[0]] == None:
                        all_answers[a[0]] = False
                    else:
                        all_answers[a[0]] &= False
        assert len(all_answers) == len(answers)
        equal = [aa == a for aa, a in zip(all_answers, answers)]
        if not all(equal):
            from IPython import embed; embed(); raise ValueError()
            print("Test FAIL for note sequence {}".format(fig_name))
        else:
            print("Test passed for note sequence {}".format(fig_name))


def test_species2():
    print("Running test for species2...")
    all_ex = []

    # fig 26
    ex = {"notes": [["A3", "D4", "A3", "B3", "C4", "G3", "A3", "D4", "B3", "G3", "A3", "B3", "C4", "A3", "D4", "B3", "C4", "A3", "B3", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["2"] * 20 + ["4"], ["4"] * 11],
          "answers": [True if n not in [16, 18] else False for n in range(21)],
          "name": "fig26",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 33
    ex = {"notes": [["A3", "D4", "A3", "B3", "C4", "G3", "A3", "D4", "B3", "C4", "D4", "A3", "C4", "D4", "E4", "B3", "D4", "A3", "B3", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["2"] * 20 + ["4"], ["4"] * 11],
          "answers": [True] * 21,
          "name": "fig33",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 35
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["R", "D2", "D3", "A2", "C3", "A2", "B2", "A2", "G2", "B2", "D3", "E3", "F3", "C3", "E3", "B2", "D3", "D2", "A2", "C#3", "D3"]],
          "durations": [["4"] * 11, ["2"] * 20 + ["4"]],
          "answers": [True] * 21,
          "name": "fig35",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 36
    ex = {"notes": [["R", "B3", "C4", "B3", "A3", "B3", "C4", "G3", "A3", "B3", "C4", "A3", "B3", "D4", "E4", "D4", "C4", "D4", "E4"],
                    ["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"]],
          "durations": [["2"] * 18 + ["4"], ["4"] * 10],
          "answers": [True] * 19,
          "name": "fig36",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 37
    ex = {"notes": [["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"],
                    ["R", "E2", "A2", "G2", "F2", "D2", "E2", "C2", "F2", "C3", "F3", "D3", "E3", "D3", "C3", "B2", "A2", "D3", "E3"]],
          "durations": [["4"] * 10, ["2"] * 18 + ["4"]],
          "answers": [True] * 19,
          "name": "fig37",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 38
    ex = {"notes": [["R", "F3", "E3", "D3", "C3", "Bb2", "A2", "G2", "F2", "A2", "C3", "Bb2", "A2", "A3", "G3", "E3", "F3", "G3", "A3", "F3", "D3", "E3", "F3"],
                    ["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"]],
          "durations": [["2"] * 22 + ["4"], ["4"] * 12],
          "answers": [True] * 23,
          "name": "fig38",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 39
    ex = {"notes": [["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"],
                    ["R", "F2", "E2", "C2", "F2", "E2", "D2", "C2", "Bb1", "Bb2", "G2", "C3", "A2", "F2", "E2", "C2", "F2", "F1", "A1", "D2", "C2", "E2", "F2"]],
          "durations": [["4"] * 12, ["2"] * 22 + ["4"]],
          "answers": [True] * 23,
          "name": "fig39",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 40
    ex = {"notes": [["R", "G3", "E3", "F3", "G3", "A3", "B3", "A3", "G3", "C4", "B3", "C4", "D4", "C4", "B3", "A3", "G3", "F3", "E3", "C4", "B3", "A3", "G3", "D3", "E3", "F#3", "G3"],
                    ["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"]],
          "durations": [["2"] * 26 + ["4"], ["4"] * 14],
          "answers": [True] * 27,
          "name": "fig40",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 41
    ex = {"notes": [["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"],
                    ["R", "G2", "E2", "F2", "G2", "F2", "E2", "D2", "C2", "E2", "C2", "C3", "B2", "A2", "G2", "B2", "C3", "B2", "A2", "G2", "F#2", "D2", "G2", "B1", "D2", "F#2", "G2"]],
          "durations": [["4"] * 14, ["2"] * 26 + ["4"]],
          "answers": [True] * 27,
          "name": "fig41",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 42
    ex = {"notes": [["R", "A3", "E3", "F3", "G3", "D3", "E3", "E4", "C4", "B3", "A3", "F3", "G3", "B3", "D4", "A3", "C4", "E3", "F#3", "G#3", "A3"],
                    ["A2", "C3", "B2", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"]],
          "durations": [["2"] * 20 + ["4"], ["4"] * 11],
          "answers": [True] * 21,
          "name": "fig42",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 43
    ex = {"notes": [["A2", "C3", "B2", "D3", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"],
                    ["R", "A1", "A2", "E2", "G2", "E2", "D2", "F2", "A2", "B2", "C3", "C2", "D2", "A1", "C2", "E2", "F2", "G2", "A2", "A1", "E2", "G#2", "A2"]],
          "durations": [["4"] * 12, ["2"] * 22 + ["4"]],
          "answers": [True] * 23,
          "name": "fig43",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 44
    ex = {"notes": [["R", "G3", "C4", "B3", "A3", "D4", "B3", "A3", "G3", "B3", "C4", "D4", "E4", "D4", "C4", "B3", "A3", "B3", "C4", "G3", "A3", "B3", "C4"],
                    ["C3", "E3", "F3", "G3", "E3", "A3", "G3", "E3", "F3", "E3", "D3", "C3"]],
          "durations": [["2"] * 22 + ["4"], ["4"] * 12],
          "answers": [True] * 23,
          "name": "fig44",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 45
    ex = {"notes": [["C3", "E3", "F3", "G3", "E3", "A3", "G3", "E3", "F3", "E3", "D3", "C3"],
                    ["R", "C2", "C3", "B2", "A2", "D3", "B2", "G2", "C3", "B2", "A2", "C3", "E3", "D3", "C3", "A2", "D3", "A2", "C3", "C2", "G2", "B2", "C3"]],
          "durations": [["4"] * 12, ["2"] * 22 + ["4"]],
          "answers": [True] * 23,
          "name": "fig45",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    for ex in all_ex:
        notes = ex["notes"]
        durations = ex["durations"]
        answers = ex["answers"]
        fig_name = ex["name"]
        ig = [ex["cantus_firmus_voice"],]
        parts = notes_to_midi(notes)
        key_signature = "C"
        time_signature = "4/4"
        aok = analyze_2voices(parts, durations, key_signature, time_signature,
                              species="species2", cantus_firmus_voices=ig)
        aok_lu = aok[1]
        aok_rules = aok[2]

        all_answers = [-1] * len(answers)

        for a in aok[-1]:
            if all_answers[a[0]] == -1:
                all_answers[a[0]] = a[1]
            else:
                if a[1] in [None, True]:
                    if all_answers[a[0]] == None:
                        all_answers[a[0]] = True
                    else:
                        all_answers[a[0]] &= True
                else:
                    if all_answers[a[0]] == None:
                        all_answers[a[0]] = False
                    else:
                        all_answers[a[0]] &= False
        assert len(all_answers) == len(answers)
        equal = [aa == a for aa, a in zip(all_answers, answers)]
        if not all(equal):
            print("Test FAIL for note sequence {}".format(fig_name))
        else:
            print("Test passed for note sequence {}".format(fig_name))


def test_species3():
    print("Running test for species3...")
    all_ex = []

    # fig 55
    ex = {"notes": [["D3", "E3", "F3", "G3", "A3", "B3", "C4", "D4", "E4", "D4", "B3", "C4", "D4", "C4", "Bb3", "A3", "Bb3", "C4", "D4", "E4", "F4", "F3", "A3", "Bb3", "C4", "A3", "Bb3", "C4", "Bb3", "A3", "G3", "Bb3", "A3", "D3", "E3", "F3", "G3", "A3", "B3", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["1"] * 40 + ["4"], ["4"] * 11],
          "answers": [True] * 41,
          "name": "fig55",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["D2", "E2", "F2", "G2", "A2", "D2", "A2", "B2", "C3", "B2", "G2", "A2", "B2", "A2", "G2", "F2", "E2", "E3", "B2", "C3", "D3", "A2", "D2", "E2", "F2", "G2", "A2", "B2", "C3", "D3", "E3", "C3", "D3", "A2", "D2", "D3", "C#3", "A2", "B2", "C3", "D3"]],
          "durations": [["4"] * 11, ["1"] * 40 + ["4"]],
          "answers": [True] * 41,
          "name": "fig56",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    for ex in all_ex:
        notes = ex["notes"]
        durations = ex["durations"]
        answers = ex["answers"]
        fig_name = ex["name"]
        ig = [ex["cantus_firmus_voice"],]
        parts = notes_to_midi(notes)
        key_signature = "C"
        time_signature = "4/4"
        aok = analyze_2voices(parts, durations, key_signature, time_signature,
                              species="species3", cantus_firmus_voices=ig)
        aok_lu = aok[1]
        aok_rules = aok[2]

        all_answers = [-1] * len(answers)

        for a in aok[-1]:
            if all_answers[a[0]] == -1:
                all_answers[a[0]] = a[1]
            else:
                if a[1] in [None, True]:
                    if all_answers[a[0]] == None:
                        all_answers[a[0]] = True
                    else:
                        all_answers[a[0]] &= True
                else:
                    if all_answers[a[0]] == None:
                        all_answers[a[0]] = False
                    else:
                        all_answers[a[0]] &= False
        all_answers = [True if aa == None else aa for aa in all_answers]
        assert len(all_answers) == len(answers)
        equal = [aa == a for aa, a in zip(all_answers, answers)]
        if not all(equal):
            print("Test FAIL for note sequence {}".format(fig_name))
        else:
            print("Test passed for note sequence {}".format(fig_name))
    from IPython import embed; embed(); raise ValueError()



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Demo of utils")

    parser.add_argument('-p', action="store_true", default=False)
    args = parser.parse_args()
    print_it = args.p
    if not print_it:
        #test_species1()
        #test_species2()
        test_species3()
    else:
        # fig 5, gradus ad parnassum
        notes = [["A3", "A3", "G3", "A3", "B3", "C4", "C4", "B3", "D4", "C#4", "D4"],
                 ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]]
        clefs = ["treble", "treble"]
        parts = notes_to_midi(notes)
        interval_figures = intervals_from_midi(parts, durations)
        durations = [[4.] * len(notes[0]), [4.] * len(notes[1])]
        # can add harmonic nnotations as well to plot
        #chord_annotations = ["i", "I6", "IV", "V6", "I", "IV6", "I64", "V", "I"]
        time_signatures = [(4, 4), (4, 4)]
        pitches_and_durations_to_pretty_midi([parts], [durations],
                                             save_dir="samples",
                                             name_tag="sample_{}.mid",
                                             default_quarter_length=240,
                                             voice_params="piano")
        plot_pitches_and_durations(parts, durations,
                                   interval_figures=interval_figures,
                                   use_clefs=clefs)
