/*
 * Generic chart routines for data_chart.cgi
 *
 * Note: We subtract .5 from all measurements that need to be centered on the pixel, instead of centered between the pixels.
 */
//Data Chart Canvas Graph (DCCG)
DCCG = {


    /* Graphing Constants */
    FONT_SIZE: 10,//9, //Global font size (px) to use to render the chart
    FONT_SIZE_BIG: 10, //Global font size (px) to use to render the chart
    FONT_SIZE_TITLE: 14, //Global font size (px) to use to render the chart
    BAR_HEIGHT: 7, //The height of each bar in the barchart (in px)
    PLOT_HEIGHT: 7, //The height of each line of plotted points in the plotchart (in px)
    //BAR_GAP: 2, // The gap distance, in px, between each bar.  A value of 0 results in each bar being pefectly adjacent.
    DATA_GAP: 2, // The gap distance, in px, between each line of data.  A value of 0 results in each data space being pefectly adjacent.
    BAR_TICK_LENGTH: 5, //The length of the tick mark at the left of the bars, between the text and the bar.

    //Draws the title for the charts - centered and at the top.
    drawChartTitle:function(ctx,title) {
        ctx.save();

        ctx.font = this.FONT_SIZE_TITLE +"px Arial, sans-serif";
        ctx.textAlign = "center";
        ctx.fillStyle = "rgba(0, 0, 0, 1)";
        ctx.fillText(title,ctx.canvas.width/2,5 + this.FONT_SIZE_TITLE); //-3 for spacing

        ctx.restore();
        return true;
    },

   /* Function: Used to render the tall version of the chart, in a verticle orientation.
    * ctx is the context of the canvas object
    * data is an object holding all the values.
    * type is 'bar' or 'plot'
    *
    * TODO: Fill the data structure note out more.
    * We also need to account for the width of the canvas to be too small to display names.
    *
    *
    *
    * Returns a mousemap
    */
    renderChartTall:function(ctx,data,type) {
        if (ctx == null) {
            //console.log("No canvas...");
            // No canvas
            return null
        };

        var vals = data;

        //Bring in a few chart measurements.
        var bar_gap = this.DATA_GAP;
        var chart_height = (bar_gap+this.BAR_HEIGHT)*vals.length+bar_gap;
        var chart_header = this.FONT_SIZE*2 + this.FONT_SIZE_TITLE +10; //space for the title, and two lines of text beneith it.
        var chart_footer = 50; //a little arbitrary.

        //This important measurement is the maximum length of all the sample names.
        var max_text_length = data.maxTxtLen;

        //resize the canvas in the y direction to accomodate all the data.
        ctx.canvas.height = chart_height + chart_header + chart_footer + 10; //add 10 for good measure.

        //Get a blank slate - this may need to be changed in the future to speed things up,
        //but the routines right now are very fast.
        this.clearCanvas(ctx); //Added note: We have to blank the canvas, even though the resize would normally do it (due to draw bug in FF).

        //Start by printing the title.
        this.drawChartTitle(ctx,data.id);

        //We set the size of the font once, and it doesn't change (for now).
        ctx.font = this.FONT_SIZE +"px Arial, sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = "rgba(0, 0, 0, 1)";

        //We start with the rounded max val.  We jump to the zoom value if it exists.
        //The rounded value should be something nice and clean (use 100 instead of 95, etc)
        var max_val = data.roundedMaxVal;
        var min_val = data.roundedMinVal;

        if (data.zoomMaxVal != null) {
            max_val = data.zoomMaxVal;
        }
        if (data.zoomMinVal != null) {
            min_val = data.zoomMinVal;
        }

        //setup chart boundaries, etc.

        //The x value that the chart bars should start at. Note that the tick marks extend negatively over the chart
        var chartx = max_text_length+2+this.BAR_TICK_LENGTH;
        var charty = chart_header; //The y value that the chart should start at.

        ctx.canvas.width = $("#dataChartTabPanel").width();
        var chart_width = ctx.canvas.width - chartx - 25;

        //Need to have a more robust rounding algorithm - this is used to round all datapoint values.
        roundVal = Math.pow(10,Math.round(Math.log(max_val)/Math.log(10))*-1+3); //This can account for rounding very small numbers
        if (roundVal < 10){roundVal = 10} //two decimal points at a minimum.

        //build the outside border of the graph.
        ctx.strokeStyle = "rgba(0, 0, 0, 1)";
        ctx.strokeRect(chartx-.5, charty-.5, chart_width,chart_height);

        //Place the max value label (and tick).
        ctx.fillStyle = "rgba(0, 0, 0, 1)";
        ctx.textAlign = "right";
        ctx.fillText(Math.round(max_val*roundVal)/roundVal,chartx+chart_width,charty-3); //-3 for spacing

        //Now for the minimum value label (and tick)
        ctx.textAlign = "center";
        ctx.fillText(Math.round(min_val*roundVal)/roundVal,chartx,charty-3);

        //Now we Build all the bars
        //We have to convert the data scale to the pixel scale, this measurement helps with that calc.
        var chart_data_width = max_val-min_val;

        //Before we actually build the bars, we need to add in the gridlines
        var grid_text_y = charty-12;
        var grid_color = "rgba(0, 0, 0, .75)";
        ctx.fillStyle = grid_color;
        ctx.textAlign = "center";

        //draw 0 line, but only if we have negative values..
        if (min_val < 0) {
            var zero_percentage = (0-min_val)/chart_data_width;
            if (zero_percentage >= 0 && zero_percentage <= 1) { //Don't display if we are off the chart bounds.
                this.drawVertGridLine(ctx,chartx,charty-8,chart_width,zero_percentage,chart_height+8,grid_color);
                var zero_center = Math.round((chart_width) * zero_percentage);
                ctx.fillText("0",chartx + zero_center,grid_text_y);
            }
        }

        //lighten up non-zero gridline.
        grid_color = "rgba(0, 0, 0, .5)";
        ctx.fillStyle = grid_color;
        ctx.textAlign = "center";

        //Draw other gridlines..
        var gridlines = this.CalcGridLines(min_val,max_val)

        for (var i = 0; i < gridlines.length; i++) {
            if (gridlines[i] == 0) {continue; }; //already drew it

            var gperc = (gridlines[i] - min_val)/chart_data_width;
            if (gperc >= 0 && gperc <= 1) { //Don't display if we are off the chart bounds.
                this.drawVertGridLine(ctx,chartx,charty-8,chart_width,gperc,chart_height+8,grid_color);
                var grid_center = Math.round((chart_width) * gperc);
                var tmp_format_num = new Number(gridlines[i])
                ctx.fillText(tmp_format_num.toPrecision(3),chartx + grid_center,grid_text_y);
            }
        }

        var dataMap;
        //Now call the function to loop through the data and draw all the bars.
        if (type == null || type == 'bar') {
            dataMap = this.drawChartBars(ctx,vals,chartx,charty,chart_width,max_val,min_val);
        } else if (type == 'plot') {
            dataMap = this.drawChartPlotLines(ctx,vals,chartx,charty,chart_width,max_val,min_val);
        }
        //Add in some median information (or mean info, if that is all we have).
        //Pick up the global mean,  If the median exists, then we use it instead.
        var global_m_title = "Mean";
        var global_m = data.globalMean;

        if (data.Median != null) {
            global_m_title = "Median";
            global_m = data.Median;
        }

        this.drawMedianLines(ctx,global_m_title,global_m,chartx,chart_width,charty,chart_height,max_val,min_val);

        //Now we need to add any labels that sit over the graph.
        this.drawCharLabels(ctx,vals,chartx,charty);

        return dataMap;
    },

    /* Draw Chart Labels - Draws all the labels sitting over the top of the bar or plot charts.
    *
    */
    drawCharLabels:function(ctx,vals,chartx,charty) {
        //Holds the current position that the label should start at - same as before basically..
        bar_y = charty + this.DATA_GAP;

        // We might be able to clean this up..
        for (var i = 0; i < vals.length; i++) {

            var mark = vals[i].Mark; //Should this sample be highlighted?

            var val = null;
            var err = null;
            if (vals[i].mean < 1 && vals[i].mean > -1 ) {
                //fractional value, so we have to round it more properly.
                val = (new Number(vals[i].mean)).toPrecision(3);
            } else {
                val = (new Number(vals[i].mean)).toFixed(2);
            }
            if (vals[i].stderr < 1 && vals[i].stderr > -1 ) {
                //fractional value, so we have to round it more properly.
                err = (new Number(vals[i].stderr)).toPrecision(3);
            } else {
                err = (new Number(vals[i].stderr)).toFixed(2);
            }

            //Show a highlight.
            if (vals[i].Mouseover == true) {
                this.drawLabel(ctx,chartx + 9.5,bar_y,this.BAR_HEIGHT,val,3,mark);
            }
            //show the stuck on value, in relation to the x-axis where it is clicked (or defined by the user).
            if (vals[i].Selected != null && vals[i].Selected > 0) {
                this.drawLabel(ctx,vals[i].Selected,bar_y,this.BAR_HEIGHT,val+"+/-"+err,3,mark);
            }
            //increment to the next y value location.
            bar_y += this.DATA_GAP;
            bar_y += this.BAR_HEIGHT;


        }//end bar creation loop.
    },

    /* Draw Chart Plot Lines - Draws the guts of the plot chart, including the data names ,but not the labels.
    *
    * returns a mousemap object.
    * Each entry in the array can have the following fields:
    * .column_name: The Name of the data
    * .Mark: A non-null, or non-false indicates that this value should be highlighted
    * .mean: The value to display (this is usually a mean of points - these are displayed on the plot chart)
    * .stderr: If there is any error with the measurement include it here.
    * .RawValues: (ARRAY) A list of numbers to be displayed on the plot.
    */
    drawChartPlotLines:function(ctx,vals,chartx,charty,chart_width,max_val,min_val) {
        ctx.save();
        //The mousemap for the chart - for mouse over and clicking info.
        var chart_data_width = max_val - min_val;
        var dataMap = new Array();

        //Holds the current position that the bar should start at.
        //we apply the gap around the outside of each bar, but only once between bars.
        var bar_y = charty + this.DATA_GAP;

        //So now we loop through all the data and build all the bars.

        for (var i = 0; i < vals.length; i++) {

            var txt = vals[i].column_name; //text of the sample

            // draw name of the sample on the chart.
            this.drawSampleName(ctx,bar_y,chartx,txt,vals[i].Mark);

            //Now draw each point of the raw data.
            var rawVals = vals[i].RawValues;

            for (var j =0; j < rawVals.length; j++) {
                //this function takes care of drawing the point for us.
                this.drawPlotPoint(ctx,chartx,bar_y,chart_width,(rawVals[j]-min_val)/chart_data_width,vals[i].color_idx);

            }

            //We might want to display the mean and error on the graph too at some point, but not right now.

            var err = vals[i].stderr;
            var val = vals[i].mean;

            if (err >0 && err + val > min_val && err-val < max_val) { //make sure we have an error to draw, and that the error is within bounds.


                var perErrL = ((val - err) - min_val)/chart_data_width;
                var perErrR = ((val + err) - min_val)/chart_data_width;
                var perErrM = ((val) - min_val)/chart_data_width;

                var pixErrL = chartx;
                if (perErrL > 0) {
                    pixErrL = Math.round(chartx + (chart_width * perErrL));
                }

                var pixErrR = chartx+chart_width;
                if (perErrR < 1) {
                    pixErrR = Math.round(chartx + (chart_width * perErrR));
                }
                var pixErrM = Math.round(chartx + (chart_width * perErrM));

                ctx.fillStyle = "rgba(210,105,30,255)"; //"rgba(0, 0, 0, 1)";
                ctx.beginPath();
                ctx.rect(pixErrL, bar_y+this.PLOT_HEIGHT/2 -1, pixErrR-pixErrL, 1);

                if (perErrL < 1 && perErrL > 0) {
                    //Make sure that the error bar end cap should be on the graph.
                    ctx.rect(pixErrL, bar_y-.5, 1, this.PLOT_HEIGHT);
                }
                if (perErrR < 1 && perErrR > 0) {
                    //Make sure that the error bar end cap should be on the graph.
                    ctx.rect(pixErrR, bar_y-.5, 1,this.PLOT_HEIGHT);
                }
                ctx.closePath();
                ctx.fill();
                //Draw the mean location.
                ctx.closePath();
                ctx.fill();
                if (perErrM < 1 && perErrM > 0) {
                    ctx.fillStyle = "rgba(110,55,15,255)"; //"rgba(0, 0, 0, 1)";
                    ctx.beginPath();
                    ctx.rect(pixErrM - 1, bar_y+this.PLOT_HEIGHT/2 -2, 3, 3);
                    ctx.closePath();
                    ctx.fill();
                }

            }


            //Add this entry to the Mouse Map returned object.
            dataMap.push({
                    dataNum: i, //Array number of the data point.
                    yStart: bar_y-1, //start of the y coordinate.
                    yEnd: bar_y+this.BAR_HEIGHT, //end of the y coordiante.
                    xStart: 0, //start of the y coordinate.
                    xEnd:  ctx.canvas.width//end of the y coordiante.
            });
            //increment to the next y value location.
            bar_y += this.DATA_GAP;
            bar_y += this.PLOT_HEIGHT;

        }//end bar creation loop.

        ctx.restore();

        return dataMap;

    },

    /*This function draws horizontal data bars for the verticle bar chart.
    * Inputs:
    * ctx is the canvas context
    * xstart and ystart are the upper left dimension of the current line.
    * c_width - the width of the chart (remember that the height of the data is constant)
    * pVal - the percentage distance that the point should be plotted at.
    * color_idx - The array index of the color used for the bar.
    */
    drawPlotPoint:function(ctx,xstart,ystart,c_width,pVal,color_idx) {
        if (ctx == null) {return false};
        ctx.save();
        var pHeight = this.PLOT_HEIGHT; //height of the plot space in pixels.
        //draw the little tick mark - this can always be done regardless of the values.
        ctx.fillStyle = "rgba(0, 0, 0, 1)";
        ctx.beginPath();
        //Entends negatively over the chartx value.
        ctx.rect(xstart-.5 - this.BAR_TICK_LENGTH, ystart+pHeight/2 -1, this.BAR_TICK_LENGTH, 1);
        ctx.closePath();
        ctx.fill();
        if (pVal < 0 || pVal > 1) { return false;}; //Can't draw what doesn't lie within..

        //Find the pixel position of the center of the plot.
        plotCenter = Math.round(xstart + (c_width * pVal));

        ctx.fillStyle = DCCG.getRGBColorFromHex(color_idx);
        ctx.beginPath();

        //Quick lesson on arc: (x,y,Radius,StartAngleInRads,EndAngleInRads,AntiClockWise?)
        ctx.arc(plotCenter,ystart+pHeight/2-1,pHeight/2,0,Math.PI*2,false);
        ctx.fill();

        ctx.strokeStyle = "rgba(0, 0, 0, .8)";
        ctx.beginPath();
        ctx.arc(plotCenter,ystart+pHeight/2-1,pHeight/2,0,Math.PI*2,false);
        ctx.stroke();



        ctx.restore();
        return true;
    },

    /*Draw Sample Name - draws the name of the sample in the correct location - very simple.
    *
    */
    drawSampleName:function(ctx,ystart,xstart,txt,mark) {
        ctx.save();
        //Potentially apply highlighting to text.
        if (mark == null || mark == false) {
            ctx.fillStyle = "rgba(0, 0, 0, 1)";
            ctx.strokeStyle = "rgba(0, 0, 0, 1)";
        } else {
            ctx.fillStyle = "rgba(250, 0, 0, 1)";
            ctx.strokeStyle = "rgba(250, 0, 0, 1)";
        }
        ctx.textAlign = "right";

        ctx.fillText(txt,xstart -2 - this.BAR_TICK_LENGTH, ystart + this.FONT_SIZE -4); //Add seven to account for font height and Don't forget to account for the tick marks!
        ctx.restore();
        return true;
    },

    /* Draw Chart Bars - Draws the guts of the bar chart, including the data names, but not the labels.
    *
    * returns a mousemap object.
    * Each entry in the array can have the following fields:
    * .column_name: The Name of the data
    * .Mark: A non-null, or non-false indicates that this value should be highlighted
    * .mean: The value to display (this is usually a mean of points - these are displayed on the plot chart)
    * .stderr: If there is any error with the measurement include it here.
    *
    */
    drawChartBars:function(ctx,vals,chartx,charty,chart_width,max_val,min_val) {
        ctx.save();
        //The mousemap for the chart - for mouse over and clicking info.
        var chart_data_width = max_val - min_val;
        var dataMap = new Array();

        //Holds the current position that the bar should start at.
        //we apply the gap around the outside of each bar, but only once between bars.
        var bar_y = charty + this.DATA_GAP;

        //So now we loop through all the data and build all the bars.

        for (var i = 0; i < vals.length; i++) {

            var txt = vals[i].column_name; //text of the sample

            //We convert single values to value ranges here,  Positive values are 0 to value,
            //negative values are value to 0.  we also tack on the error bar.
            var vStart;
            var vEnd;

            var val = vals[i].mean;

            var err = vals[i].stderr;


            if (val >= 0) {
                err = val + err;
                if (vals[i].Max != null && vals[i].Max > err) {
                    err = vals[i].Max;
                }
                vStart = 0;
                vEnd = val;

            } else {
                err = val - err;
                vStart = val;
                vEnd = 0;
            }

            //this function takes care of drawing the data bar, error bar, and the tickmark.
            this.draw_hbar(ctx,chartx,bar_y,chart_width,(vStart-min_val)/chart_data_width,(vEnd-min_val)/chart_data_width,(err-min_val)/chart_data_width,vals[i].color_idx);

            //draw label for sample.
            this.drawSampleName(ctx,bar_y,chartx,txt,vals[i].Mark);


            //WE NOW DRAW LABELS IN A SECOND LOOP.


            //Add this entry to the Mouse Map returned object.
            dataMap.push({
                    dataNum: i, //Array number of the data point.
                    yStart: bar_y-1, //start of the y coordinate.
                    yEnd: bar_y+this.BAR_HEIGHT, //end of the y coordiante.
                    xStart: 0, //start of the y coordinate.
                    xEnd:  ctx.canvas.width//end of the y coordiante.
            });
            //increment to the next y value location.
            bar_y += this.DATA_GAP;
            bar_y += this.BAR_HEIGHT;

        }//end bar creation loop.

        ctx.restore();

        return dataMap;

    },

    drawChartBox:function(ctx) {
        return null;

    },

    //Used to draw median (or mean) lines on the chart.
    drawMedianLines:function(ctx,title,global_m,chartx,chart_width,charty,chart_height,max_val,min_val) {
        ctx.save();
        //Figure out the data width for percentage calcs.
        var chart_data_width = max_val-min_val;

        //Set drawing parameters for these lines.
        var median_color = "rgba(150, 0, 150, 1)";


        ctx.fillStyle = median_color;
        ctx.textAlign = "center";

        var median_percentage = (global_m-min_val)/chart_data_width;
        var median_percentagex3 = (global_m*3-min_val)/chart_data_width;
        var median_percentagex10 = (global_m*10-min_val)/chart_data_width;
        var median_percentagex30 = (global_m*30-min_val)/chart_data_width;
        if (median_percentage >= 0 && median_percentage <= 1) { //Don't display if we are off the chart bounds.
            this.drawVertGridLine(ctx,chartx,charty,chart_width,median_percentage,chart_height+10,median_color);
            var median_center = Math.round((chart_width) * median_percentage);
            ctx.fillText(title + "("+Math.round(global_m*roundVal)/roundVal+")",chartx + median_center,charty+chart_height+20);
        }
        if (median_percentagex3 >= 0 && median_percentagex3 <= 1 && median_percentagex3 != median_percentage) { //Don't display if we are off the chart bounds.
            this.drawVertGridLine(ctx,chartx,charty,chart_width,median_percentagex3,chart_height+10,median_color);
            var median_center = Math.round((chart_width) * median_percentagex3);
            ctx.fillText("3xM",chartx + median_center,charty+chart_height+30);
        }
        if (median_percentagex10 >= 0 && median_percentagex10 <= 1 && median_percentagex10 != median_percentage) { //Don't display if we are off the chart bounds.
            this.drawVertGridLine(ctx,chartx,charty,chart_width,median_percentagex10,chart_height+10,median_color);
            var median_center = Math.round((chart_width) * median_percentagex10);
            ctx.fillText("10xM",chartx + median_center,charty+chart_height+30);
        }
        if (median_percentagex30 >= 0 && median_percentagex30 <= 1 && median_percentagex30 != median_percentage) { //Don't display if we are off the chart bounds.
            this.drawVertGridLine(ctx,chartx,charty,chart_width,median_percentagex30,chart_height+10,median_color);
            var median_center = Math.round((chart_width) * median_percentagex30);
            ctx.fillText("30xM",chartx + median_center,charty+chart_height+30);
        }

        ctx.restore();
    },

    drawLabel:function(ctx, xCoord, yCoord, yHeight, text, padding, highlight) {

        //We are nice to the calling script - we save and restore the canvas state so it is like we never touched it.
        ctx.save();

        //delte me later - this is just for the conversion to keep track of vars.
        //var x_tag = xCoord;
        //var rMean = text;
        //var mark = highlight;
        //var bar_y = yCoord;

        ctx.textAlign = "left";
        ctx.font = this.FONT_SIZE_BIG +"px Arial, sans-serif";

        var tLen = this.textLenBig(ctx,text);

        if (highlight == null || highlight == false) {
            ctx.fillStyle = "rgba(255, 255, 255, .65)";
        } else {
            ctx.fillStyle = "rgba(255, 255, 0, .80)";
        }

        //Draw the square behind the text
        ctx.beginPath();
        ctx.rect(xCoord, yCoord - (padding-.5), tLen + 2*padding, this.BAR_HEIGHT+padding);
        ctx.closePath();
        ctx.fill();

        //draw the black border, potentially applying highlighting.
        if (highlight == null || highlight == false) {
            ctx.strokeStyle = "rgba(0, 0, 0, 1)";
        } else {
            ctx.strokeStyle = "rgba(0, 0, 250, 1)";
        }
        ctx.strokeRect(xCoord, yCoord -(padding-.5), tLen + 2* padding, this.BAR_HEIGHT+ padding);

        if (highlight == null || highlight == false) {
            ctx.fillStyle = "rgba(0, 0, 0, 1)";
        } else {
            ctx.fillStyle = "rgba(200, 0, 0, 1)";
        }

        ctx.fillText(text,xCoord + padding, yCoord + 6); //Add seven to account for font height.

        ctx.restore(); //return the canvas to the previous state to be nice.
        return true;

    },

   //This is the main function call to render a plot chart.  It is pretty much just like a bar chart only we
   //draw all the circles for each data point instead of using the mean of the Values.
    renderPlotChartTall:function(ctx,data) {
        var dataMap = this.renderBarChartTall(ctx,data);
        return dataMap;
    },

    //function to save the contents of the canvas as an image.
    saveCanvas:function(ctx) {

        var myWin = window.open();
        myWin.document.write("<p>Right click and select 'Save image'.</p><img src='' id='save_png' alt='Datachart Image' />");
        var dest_img = myWin.document.getElementById('save_png');
        dest_img.src = ctx.canvas.toDataURL('image/png');

    },

    CalcGridLines:function(min, max) {
        //returns an array of values donoting where gridlines should lie.
        var gridvals = new Array();

        //No point in gridlines if there is no separation.
        if (max <= min) {
            return gridvals;
        }

        var base = Math.floor(Math.log(max - min)/Math.log(10));


        var tenToBase = Math.pow(10,base);

        var maxBase = Math.round(max / tenToBase);
        var minBase = Math.floor(min / tenToBase);

        var span = (maxBase - minBase)*tenToBase;

        span = Math.round(span/tenToBase);

        var increment = 1;

        if (span >= 8) {
            increment = 2.5 ;
        }else if (span >= 6) {
            increment = 2.0;
        }else if (span >= 4) {
            increment = 1;
        }else if (span >= 3) {
            increment = .5;
        }else if (span >= 2) {
            increment = .4;
        }else {
            increment = .25;
        }

        var start = Math.floor(minBase/increment)*increment;
        //now spit out the grid lines
        var cur_val = start;
        for (var i = 0; i < 10; i++) {
            //have to add some rounding since the math isn't so great in javascript (2.00000000001 stuff)
            var grid = Math.round(cur_val*100)/100 * tenToBase;
            if (grid > min && grid < max) {
                gridvals.push(grid);

            }
            cur_val = cur_val + increment;

        }
        return gridvals;

    },

    //Quick function to clear the canvas.
    clearCanvas:function(ctx) {
        //ctx.clearRect(0,0, ctx.canvas.width, ctx.canvas.height);
        ctx.fillStyle = "rgba(255, 255, 255, 1)";
        ctx.fillRect(0,0, ctx.canvas.width, ctx.canvas.height);
    },

    //Quick function to determine the length of a text string at the standard font size.
    textLen:function(ctx,txt) {
        ctx.font = this.FONT_SIZE +"px Arial, sans-serif";
        return ctx.measureText(txt).width;
    },
    textLenBig:function(ctx,txt) {
        ctx.font = this.FONT_SIZE_BIG +"px Arial, sans-serif";
        return ctx.measureText(txt).width;
    },

    //Draws a verticle Line on the chart.  Used for Grid Lines and Also median lines.
    drawVertGridLine:function(ctx,xstart,ystart,max_length,percentage,y_length,colorString) {
        if (ctx == null) {return false}; //Can't do anything without a canvas.

        //Note that percentage is based on how far along max_length the line should occure.
        //calculate the x-pixel start position
        var x_val = Math.round((max_length) * percentage); //accounts for the tick mark.

        //First we need to set the color
        ctx.fillStyle = colorString;

        //Now we need to draw the bar
        ctx.beginPath();
        ctx.rect(xstart+x_val, ystart-.5, 1, y_length);
        ctx.closePath();

        ctx.fill();
        return true;
    },

    //This function draws horizontal data bars for the verticle bar chart.
    // Inputs:
    // ctx is the canvas context
    // xstart and ystart are the upper left dimension of the chart.
    // c_width - the width of the chart (remember that the height of the bar is constant)
    // pStart - the percentage distance that the left side of the bar starts at
    // pEnd - the percentage distance that the right side of the bar ends at
    // Note that pStart must be less than pEnd.
    // pError - the percentage distance that the end of the error bar occurs at.
    // color_idx - The array index of the color used for the bar.
    draw_hbar:function(ctx,xstart,ystart,c_width,pStart,pEnd,pError,color_idx) {
        if (ctx == null) {return false};


        var bHeight = this.BAR_HEIGHT; //height of the bar in pixels.
        //draw the little tick mark - this can always be done regardless of the values.
        ctx.fillStyle = "rgba(0, 0, 0, 1)";
        ctx.beginPath();
        //Entends negatively over the chartx value.
        ctx.rect(xstart-.5 - this.BAR_TICK_LENGTH, ystart+bHeight/2 -1, this.BAR_TICK_LENGTH, 1);
        ctx.closePath();
        ctx.fill();

        if (pStart > pEnd) { return false}; //This is a no no..

        //Find the pixel position of the left side of the data bar.
        var bStart = xstart; //assume we are less than the left bound to start.
        if (pStart >= 0 && pStart <= 1) {
            bStart = Math.round(xstart + (c_width * pStart)); //within bounds so convert to pixel.
        } else if ( pStart > 1) {
            bStart = null; //our left part of the bar is over the right boundary of the graph.  We don't leave yet incase the error bar will still show.
        }

        //Now for the right side of the bar.
        var bEnd = xstart+ c_width; //Start all the way to the right bound.
        if (pEnd >= 0 && pEnd < 1) {
            bEnd = Math.round(xstart+(c_width * pEnd)); //Within bounds so convert to pixel.
        } else if (pEnd < 0){
            bEnd = null; //our right side of the bar is over the left boundary of the graph.  We don't leave yet incase the error bar will still show.
        }

        //Now we attempt to draw the bar.
        bLength = bEnd-bStart;
        if (bStart != null && bEnd != null && bLength > 0) {
            //we have valid points.  So now we can build a bar.
            //First we need the color
            ctx.fillStyle = DCCG.getRGBColorFromHex(color_idx);

            //Draw the inside of the bar
            ctx.beginPath();
            ctx.rect(bStart-.5, ystart-.5, bLength , bHeight);
            ctx.closePath();
            ctx.fill();

            //draw the black border
            ctx.strokeStyle = "rgba(0, 0, 0, .5)";
            ctx.strokeRect(bStart-.5, ystart-.5 , bLength, bHeight);

        }

        //Ok, time to draw up the error bars.
        //Since the bar can be in either orientation, we have to build mirror code to handle it.
        if (pError > pEnd) {
            //This is the case that the bar is positive, so we want to place the error bar between the right of the large bar and the value of the error percentage.
            if (pEnd >= 1 || pError <= 0 ) {
                //The end of the data bar is already off to the right, so we skip it.
                //Other case is that the right most end of the error bar is already off to the left, so we skip it too.

            } else  {
                //The data bar is either on the chart, or off to the left,  this is ok, the error bar can still show up.
                var bErrorLeft = xstart; //in case the data bar is off the left side of the chart.
                if (pEnd > 0){//The data bar is in the chart.
                    bErrorLeft = bEnd;
                }

                var bErrorRight = xstart+ c_width;
                if (pError < 1 && pError > 0) {
                    bErrorRight = Math.round(xstart + (c_width * pError))
                }
                ctx.fillStyle = "rgba(210,105,30,255)"; //"rgba(0, 0, 0, 1)";
                ctx.beginPath();
                ctx.rect(bErrorLeft, ystart+bHeight/2 -1, bErrorRight-bErrorLeft, 1);
                if (pError < 1 && pError > 0) {
                    //Make sure that the error bar end cap should be on the graph.
                    ctx.rect(bErrorRight, ystart-.5, 1, bHeight);
                }
                ctx.closePath();
                ctx.fill();
            }

        } else if (pError < pStart) {
            //Negative value case.
            if (pStart <= 0 || pError >= 1) {
                //Skip this since we are already off to the left or the left side of the error bar is alread off to the right.
            } else {
                var bErrorRight = xstart+ c_width; //in case the bar is off the right side of the chart.
                if (pStart < 1) { //Ok, the data bar is actuall on the graph, so we grab its edge.
                    bErrorRight = bStart;
                }

                var bErrorLeft = xstart;
                if (pError < 1 && pError > 0) {
                    bErrorLeft = Math.round(xstart + (c_width * pError))
                }
                ctx.fillStyle = "rgba(210,105,30,255)"; //"rgba(0, 0, 0, 1)";
                ctx.beginPath();
                ctx.rect(bErrorLeft, ystart+bHeight/2 -1, bErrorRight-bErrorLeft, 1);
                if (pError < 1 && pError > 0) {
                    //Make sure that the error bar end cap should be on the graph.
                    ctx.rect(bErrorLeft, ystart-.5, 1, bHeight);
                }
                ctx.closePath();
                ctx.fill();

            }
        } else {
            //The error percentage bar cannot be in the middle of the bar, so this is bad.
            //But we ignore it and just don't siplay anything.
        }

        return true;
    },

    //Function to display an error on the canvas - quick and dirty.
    buildCanvasError:function(ctx) {
        this.clearCanvas(ctx);

        ctx.font = "9px sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = "rgba(0, 0, 0, 1)";
        ctx.fillText("No Data to Display",10,15);
    },

    buildCanvasLoading:function(ctx) {
        this.clearCanvas(ctx);

        ctx.font = "9px sans-serif";
        ctx.textAlign = "left";
        ctx.fillStyle = "rgba(0, 0, 0, 1)";
        ctx.fillText("Loading...",10,15);
    },

    /*
        getRGBColorFromHex:
        Input is a number representing the position of a color
        in the color_codes array. Returns an rgba string with the 4 color values.
    */
    getRGBColorFromHex:function(color_num) {
        color_codes = ['9400D3', '2F4F4F', '483D8B', '8FBC8B', 'E9967A', '8B0000', '9932CC', 'FF8C00', '556B2F', '8B008B', 'BDB76B', '7FFFD4', 'A9A9A9', 'B8860B', '008B8B', '00008B', '00FFFF', 'DC143C', '6495ED', 'FF7F50', 'D2691E', '7FFF00', '5F9EA0', 'DEB887', 'A52A2A', '8A2BE2', '0000FF', '000000', 'FFE4C4', '006400', '00FFFF'];
        if (color_num > color_codes.length) {
            color_num = (color_num % color_codes.length) - 1;
        }
        var hex = color_codes[color_num];
        if (hex == undefined) {
            hex = color_codes[0];
        }

        // Convert hex color value to RGB
        var r = parseInt(hex.substring(0, 2), 16);
        var g = parseInt(hex.substring(2, 4), 16);
        var b = parseInt(hex.substring(4, 6), 16);
        return "rgba(" + r + "," + g + "," + b + ",255)";
    }
};
